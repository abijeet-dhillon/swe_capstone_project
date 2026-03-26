from __future__ import annotations
import os, shutil, tempfile
from src.api.routers.portfolio import _build_heatmap_data, _build_portfolio_ts, _build_showcase_data
from src.insights.storage import ProjectInsightsStore
from tests.insights.utils import build_pipeline_payload


def _make_store(td: str, names=("Alpha", "Beta")) -> ProjectInsightsStore:
    store = ProjectInsightsStore(db_path=os.path.join(td, "app.db"), encryption_key=b"dev")
    payload = build_pipeline_payload(project_names=names, include_presentation=True)
    for idx, name in enumerate(names):
        payload["projects"][name]["git_analysis"] = {
            "total_commits": (idx + 1) * 6, "total_contributors": idx + 1,
            "first_commit_at": f"2025-0{idx + 1}-06", "last_commit_at": f"2025-0{idx + 1}-27",
            "duration_days": 21, "activity_mix": {"code": 0.8, "doc": 0.2}, "contributors": [],
        }
        payload["projects"][name]["project_metrics"] = {
            "total_commits": (idx + 1) * 6, "duration_start": f"2025-0{idx + 1}-06",
            "duration_end": f"2025-0{idx + 1}-27", "total_lines": 100 * (idx + 1),
            "total_files": 5, "doc_files": 1, "image_files": 0, "video_files": 0,
            "test_files": 1, "total_contributors": idx + 1, "skills": ["python"],
        }
    store.record_pipeline_run(os.path.join(td, "seed.zip"), payload)
    return store


def _tmp_store():
    td = tempfile.mkdtemp()
    try:
        yield _make_store(td)
    finally:
        shutil.rmtree(td, ignore_errors=True)


_BASE = {
    "name": "T", "title": "E", "bio": "B", "email": "t@x.com", "location": "V",
    "socials": [], "about": {"description": ["B"], "highlights": []},
    "skills": [{"name": "L", "skills": ["python"]}],
    "projects": [{"title": "p", "description": "d", "tags": ["python"]}],
}


# --- _build_heatmap_data ---

def test_heatmap_data_shape():
    td = tempfile.mkdtemp()
    try:
        r = _build_heatmap_data(_make_store(td))
        assert r and "weeks" in r and "total_weeks" in r and "total_activity" in r and "date_range" in r
        assert r["total_weeks"] == len(r["weeks"])
        assert r["total_activity"] == sum(r["weeks"].values())
        assert r["date_range"]["start"] <= r["date_range"]["end"]
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_heatmap_data_none_on_empty():
    td = tempfile.mkdtemp()
    try:
        assert _build_heatmap_data(ProjectInsightsStore(db_path=os.path.join(td, "e.db"), encryption_key=b"dev")) is None
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_heatmap_data_weeks_sorted():
    td = tempfile.mkdtemp()
    try:
        r = _build_heatmap_data(_make_store(td))
        assert r and list(r["weeks"]) == sorted(r["weeks"])
    finally:
        shutil.rmtree(td, ignore_errors=True)


# --- _build_showcase_data ---

def test_showcase_data_shape():
    td = tempfile.mkdtemp()
    try:
        r = _build_showcase_data(_make_store(td), limit=3)
        assert r and r[0]["rank"] == 1
        assert all(k in r[0] for k in ("project_id", "score", "key_metrics", "evolution", "key_skills"))
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_showcase_data_ordered_by_score():
    td = tempfile.mkdtemp()
    try:
        r = _build_showcase_data(_make_store(td), limit=2)
        if r and len(r) >= 2:
            assert r[0]["score"] >= r[1]["score"]
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_showcase_data_respects_limit():
    td = tempfile.mkdtemp()
    try:
        r = _build_showcase_data(_make_store(td), limit=1)
        assert r and len(r) <= 1
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_showcase_data_none_on_empty():
    td = tempfile.mkdtemp()
    try:
        assert _build_showcase_data(ProjectInsightsStore(db_path=os.path.join(td, "e.db"), encryption_key=b"dev"), limit=3) is None
    finally:
        shutil.rmtree(td, ignore_errors=True)


# --- _build_portfolio_ts ---

def test_ts_omits_heatmap_when_absent():
    assert "heatmap:" not in _build_portfolio_ts({**_BASE})


def test_ts_embeds_heatmap():
    ts = _build_portfolio_ts({**_BASE, "heatmap": {"weeks": {"2025-01-06": 3, "2025-01-13": 5}, "total_weeks": 2, "total_activity": 8, "date_range": {"start": "2025-01-06", "end": "2025-01-13"}}})
    assert "heatmap:" in ts and '"2025-01-06": 3' in ts and "total_activity: 8" in ts


def test_ts_omits_showcase_when_absent():
    assert "showcase:" not in _build_portfolio_ts({**_BASE})


def test_ts_embeds_showcase():
    ts = _build_portfolio_ts({**_BASE, "showcase": [{"rank": 1, "project_id": 1, "project_title": "P", "score": 9.0, "summary": "s", "key_skills": ["python"], "key_metrics": {"total_files": 1, "total_lines": 10, "total_commits": 2, "total_contributors": 1, "doc_files": 0, "image_files": 0, "video_files": 0, "test_files": 0}, "evolution": {"first_commit_at": "2025-01-01", "last_commit_at": "2025-03-01", "duration_days": 59, "total_commits": 2, "contributors": [], "activity_mix": {"code": 1.0}}}]})
    assert "showcase:" in ts and '"P"' in ts and "rank: 1" in ts
