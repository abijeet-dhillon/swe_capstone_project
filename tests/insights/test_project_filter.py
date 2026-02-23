"""Tests for ProjectFilterEngine: filtering, sorting, search, and presets."""

import sqlite3
import pytest

from src.insights.storage import ProjectInsightsStore
from src.insights.project_filter import (
    ProjectFilter, ProjectFilterEngine, ProjectType, SortBy, SuccessMetrics,
)
from tests.insights.utils import build_pipeline_payload


@pytest.fixture()
def engine(tmp_path):
    db_path = str(tmp_path / "filter_test.db")
    store = ProjectInsightsStore(db_path=db_path, encryption_key=b"test-key")
    store.record_pipeline_run(str(tmp_path / "demo.zip"), build_pipeline_payload())
    return ProjectFilterEngine(db_path=db_path)


def test_roundtrip_serialization():
    f = ProjectFilter(languages=["python"], sort_by=SortBy.LOC_DESC, limit=10, offset=5)
    restored = ProjectFilter.from_dict(f.to_dict())
    assert restored.languages == ["python"]
    assert restored.sort_by == SortBy.LOC_DESC
    assert restored.limit == 10


def test_empty_filter_returns_all(engine):
    results = engine.apply_filter(ProjectFilter())
    names = {r["project_name"] for r in results}
    assert "ProjectAlpha" in names and "ProjectBeta" in names


def test_search_by_name(engine):
    results = engine.apply_filter(ProjectFilter(search_text="Alpha"))
    assert len(results) >= 1
    assert all("Alpha" in r["project_name"] for r in results)


def test_search_no_match(engine):
    assert engine.search_projects("zzz_nonexistent_zzz") == []


def test_sort_by_name_asc(engine):
    results = engine.apply_filter(ProjectFilter(sort_by=SortBy.NAME_ASC))
    names = [r["project_name"] for r in results]
    assert names == sorted(names)


def test_filter_min_lines(engine):
    all_r = engine.apply_filter(ProjectFilter())
    max_lines = max(r["total_lines"] for r in all_r)
    results = engine.apply_filter(ProjectFilter(metrics=SuccessMetrics(min_lines=max_lines)))
    assert len(results) >= 1 and all(r["total_lines"] >= max_lines for r in results)


def test_filter_max_lines_zero(engine):
    assert engine.apply_filter(ProjectFilter(metrics=SuccessMetrics(max_lines=0))) == []


def test_limit(engine):
    assert len(engine.apply_filter(ProjectFilter(limit=1))) <= 1


def test_offset(engine):
    all_r = engine.apply_filter(ProjectFilter(sort_by=SortBy.NAME_ASC))
    if len(all_r) >= 2:
        offset_r = engine.apply_filter(ProjectFilter(sort_by=SortBy.NAME_ASC, offset=1))
        assert offset_r[0]["project_name"] == all_r[1]["project_name"]


def test_preset_lifecycle(engine):
    pid = engine.save_preset("Test", ProjectFilter(languages=["python"]), description="desc")
    preset = engine.get_preset(pid)
    assert preset.name == "Test" and preset.filter_config.languages == ["python"]
    assert engine.delete_preset(pid) is True
    assert engine.get_preset(pid) is None


def test_preset_upsert(engine):
    engine.save_preset("X", ProjectFilter(limit=5))
    engine.save_preset("X", ProjectFilter(limit=10))
    assert engine.get_preset_by_name("X").filter_config.limit == 10


def test_presets_table_created(tmp_path):
    db_path = str(tmp_path / "fresh.db")
    ProjectFilterEngine(db_path=db_path)
    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='filter_presets';"
        ).fetchone() is not None
