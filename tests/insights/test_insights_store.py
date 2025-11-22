"""
Tests for the ProjectInsightsStore which persists pipeline output.
"""

import sqlite3
from pathlib import Path

import pytest

from src.insights.storage import (
    PROJECT_TABLE,
    ZIP_TABLE,
    PayloadValidationError,
    ProjectInsightsStore,
)


@pytest.fixture()
def encryption_key(monkeypatch):
    key = "unit-test-key"
    monkeypatch.setenv("INSIGHTS_ENCRYPTION_KEY", key)
    return key.encode("utf-8")


@pytest.fixture()
def temp_store(tmp_path, encryption_key):
    db_path = tmp_path / "insights.db"
    store = ProjectInsightsStore(db_path=str(db_path), encryption_key=encryption_key)
    yield store


def build_pipeline_payload(project_names=("ProjectAlpha", "ProjectBeta")):
    projects = {}
    for idx, name in enumerate(project_names):
        projects[name] = {
            "project_name": name,
            "project_path": f"/tmp/{name.lower()}",
            "is_git_repo": idx == 0,
            "git_analysis": {"total_commits": (idx + 1) * 5},
            "categorized_contents": {
                "code": [f"{name.lower()}/code.py"],
                "code_by_language": {"python": [f"{name.lower()}/code.py"]},
                "documentation": [f"{name.lower()}/README.md"],
                "images": [],
                "other": ["video/demo.mp4"],
            },
            "analysis_results": {
                "documentation": {"totals": {"total_words": 120 + idx}},
                "code": {"metrics": {"total_files": 1, "total_lines": 42 + idx}},
            },
        }
    payload = {
        "zip_metadata": {
            "root_name": "demo-root",
            "file_count": 20,
            "total_uncompressed_bytes": 12345,
            "total_compressed_bytes": 6789,
        },
        "projects": projects,
    }
    return payload


def test_record_pipeline_run_persists_rows(temp_store):
    payload = build_pipeline_payload()
    stats = temp_store.record_pipeline_run("/tmp/demo.zip", payload)
    assert stats.inserted == 2
    assert stats.project_count == 2
    assert stats.metadata_updated is True

    with sqlite3.connect(temp_store.db_path) as conn:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {ZIP_TABLE};")
        assert cursor.fetchone()[0] == 1
        cursor = conn.execute(f"SELECT COUNT(*) FROM {PROJECT_TABLE};")
        assert cursor.fetchone()[0] == 2
        blob = conn.execute(f"SELECT metadata_encrypted FROM {ZIP_TABLE};").fetchone()[0]
        assert isinstance(blob, bytes)
        assert b"demo-root" not in blob  # encryption ensures readable strings are absent


def test_incremental_updates_detect_changes(temp_store):
    payload = build_pipeline_payload()
    temp_store.record_pipeline_run("/tmp/demo.zip", payload)
    # identical run -> no updates
    stats = temp_store.record_pipeline_run("/tmp/demo.zip", payload)
    assert stats.inserted == 0
    assert stats.updated == 0
    assert stats.unchanged == 2
    assert stats.metadata_updated is False

    # mutate a single project
    mutated = build_pipeline_payload()
    mutated["projects"]["ProjectAlpha"]["analysis_results"]["documentation"]["totals"]["total_words"] = 999
    stats = temp_store.record_pipeline_run("/tmp/demo.zip", mutated)
    assert stats.updated == 1
    assert stats.unchanged == 1


def test_removed_project_is_deleted(temp_store):
    payload = build_pipeline_payload()
    temp_store.record_pipeline_run("/tmp/demo.zip", payload)
    trimmed = build_pipeline_payload(project_names=("ProjectAlpha",))
    stats = temp_store.record_pipeline_run("/tmp/demo.zip", trimmed)
    assert stats.deleted == 1
    assert stats.project_count == 1


def test_load_project_insight_returns_decrypted_payload(temp_store):
    payload = build_pipeline_payload()
    temp_store.record_pipeline_run("/tmp/demo.zip", payload)
    recent = temp_store.list_recent_zipfiles(limit=1)
    zip_hash = recent[0]["zip_hash"]
    insight = temp_store.load_project_insight(zip_hash, "ProjectAlpha")
    assert insight
    assert insight["project_name"] == "ProjectAlpha"
    assert insight["analysis_results"]["documentation"]["totals"]["total_words"] == 120


def test_backup_and_restore_round_trip(temp_store, tmp_path):
    payload = build_pipeline_payload()
    temp_store.record_pipeline_run("/tmp/demo.zip", payload)
    backup_path = tmp_path / "backup" / "insights.db"
    backup_file = temp_store.backup(str(backup_path))
    original = Path(temp_store.db_path)
    original.unlink()
    temp_store.restore(backup_file)
    assert Path(temp_store.db_path).exists()
    assert temp_store.list_recent_zipfiles()


def test_purge_expired_records(temp_store):
    payload = build_pipeline_payload()
    temp_store.record_pipeline_run("/tmp/zip_a.zip", payload)
    payload_b = build_pipeline_payload(project_names=("ProjectBeta",))
    temp_store.record_pipeline_run("/tmp/zip_b.zip", payload_b)

    # Force first record to look stale
    with sqlite3.connect(temp_store.db_path) as conn:
        conn.execute(
            f"UPDATE {ZIP_TABLE} SET updated_at = ? WHERE zip_path = ?;",
            ("2000-01-01T00:00:00+00:00", "/tmp/zip_a.zip"),
        )
        conn.commit()

    purged = temp_store.purge_expired_records(retention_days=30, keep_recent=0)
    assert purged == 1
    assert len(temp_store.list_recent_zipfiles()) == 1


def test_validation_errors_raise(temp_store):
    bad_payload = {"projects": {}}
    with pytest.raises(PayloadValidationError):
        temp_store.record_pipeline_run("/tmp/demo.zip", bad_payload)


def test_metadata_and_project_listing_helpers(temp_store):
    payload = build_pipeline_payload()
    temp_store.record_pipeline_run("/tmp/demo.zip", payload)
    zip_hash = temp_store.list_recent_zipfiles(limit=1)[0]["zip_hash"]

    metadata = temp_store.get_zip_metadata(zip_hash)
    assert metadata["root_name"] == "demo-root"
    assert metadata["file_count"] == 20

    project_names = temp_store.list_projects_for_zip(zip_hash)
    assert project_names == ["ProjectAlpha", "ProjectBeta"]
