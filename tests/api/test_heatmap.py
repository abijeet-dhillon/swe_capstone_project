"""
Tests for GET /portfolio/heatmap — weekly commit-activity heatmap endpoint.

Covers:
- Returns sorted weekly counts when projects exist (normal case)
- Aggregates activity across multiple projects
- Falls back to range-based distribution when no timeline data exists
- Returns 404 when the store is empty
- date_range start <= end and total_activity matches sum of weeks
- Timeline-based heatmap uses actual event timestamps
"""
from __future__ import annotations

import os
import shutil
import tempfile
from typing import Any, Dict

from fastapi.testclient import TestClient

from src.api import deps
from src.api.app import app
from src.api.routers.portfolio import (
    _heatmap_from_range,
    _heatmap_from_timeline,
    _iso_week_key,
    _merge_heatmaps,
    _weeks_from_range,
)
from src.insights.storage import ProjectInsightsStore
from tests.insights.utils import build_pipeline_payload


# ---------------------------------------------------------------------------
# Unit tests for pure helpers (no HTTP, no DB)
# ---------------------------------------------------------------------------

def test_iso_week_key_returns_monday():
    """A Wednesday maps back to the preceding Monday."""
    assert _iso_week_key("2025-09-03") == "2025-09-01"  # Wed → Mon


def test_iso_week_key_handles_iso_datetime():
    """Timestamps with a T separator are truncated to date before processing."""
    assert _iso_week_key("2025-09-03T14:22:00") == "2025-09-01"


def test_iso_week_key_returns_none_for_bad_input():
    assert _iso_week_key("not-a-date") is None
    assert _iso_week_key("") is None


def test_weeks_from_range_covers_full_span():
    weeks = _weeks_from_range("2025-01-06", "2025-01-20")  # Mon, Mon, Mon
    assert weeks == ["2025-01-06", "2025-01-13", "2025-01-20"]


def test_weeks_from_range_empty_on_bad_input():
    assert _weeks_from_range("bad", "2025-01-01") == []


def test_heatmap_from_timeline_counts_per_week():
    timeline = [
        {"timestamp": "2025-09-01", "file": "a.py", "category": "code", "skills": []},
        {"timestamp": "2025-09-02", "file": "b.py", "category": "code", "skills": []},
        {"timestamp": "2025-09-08", "file": "c.py", "category": "code", "skills": []},
    ]
    heatmap = _heatmap_from_timeline(timeline)
    # 2025-09-01 and 2025-09-02 are both in week starting 2025-09-01
    assert heatmap["2025-09-01"] == 2
    # 2025-09-08 is Monday of the next week
    assert heatmap["2025-09-08"] == 1


def test_heatmap_from_timeline_ignores_missing_timestamps():
    timeline = [{"file": "x.py", "category": "code", "skills": []}]
    assert _heatmap_from_timeline(timeline) == {}


def test_heatmap_from_range_distributes_commits():
    heatmap = _heatmap_from_range("2025-01-06", "2025-01-20", 7)
    assert sum(heatmap.values()) == 7
    assert len(heatmap) == 3  # three weeks


def test_heatmap_from_range_returns_empty_on_zero_commits():
    assert _heatmap_from_range("2025-01-06", "2025-01-20", 0) == {}


def test_heatmap_from_range_returns_empty_on_missing_dates():
    assert _heatmap_from_range(None, "2025-01-20", 5) == {}
    assert _heatmap_from_range("2025-01-06", None, 5) == {}


def test_merge_heatmaps_sums_overlapping_weeks():
    a = {"2025-01-06": 3, "2025-01-13": 1}
    b = {"2025-01-06": 2, "2025-01-20": 4}
    merged = _merge_heatmaps([a, b])
    assert merged["2025-01-06"] == 5
    assert merged["2025-01-13"] == 1
    assert merged["2025-01-20"] == 4


# ---------------------------------------------------------------------------
# Integration tests via HTTP client
# ---------------------------------------------------------------------------

def _make_store(td: str, project_names=("Alpha", "Beta")) -> ProjectInsightsStore:
    """Seed a DB with synthetic projects that have date-range metrics."""
    db_path = os.path.join(td, "app.db")
    store = ProjectInsightsStore(db_path=db_path, encryption_key=b"dev")
    payload = build_pipeline_payload(project_names=project_names, include_presentation=True)
    for idx, name in enumerate(project_names):
        metrics = payload["projects"][name].get("project_metrics") or {}
        metrics["total_commits"] = (idx + 1) * 4
        metrics["duration_start"] = f"2025-0{idx + 1}-06"
        metrics["duration_end"] = f"2025-0{idx + 1}-27"
        metrics["duration_days"] = 21
        payload["projects"][name]["project_metrics"] = metrics
    store.record_pipeline_run(os.path.join(td, "seed.zip"), payload)
    return store


def test_heatmap_returns_sorted_weeks_and_summary():
    """Normal case: returns weeks dict, total_weeks, total_activity, date_range."""
    td = tempfile.mkdtemp()
    try:
        store = _make_store(td)
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/heatmap")

        assert resp.status_code == 200
        data = resp.json()
        assert "weeks" in data
        assert "total_weeks" in data
        assert "total_activity" in data
        assert "date_range" in data
        assert data["total_weeks"] == len(data["weeks"])
        assert data["total_activity"] == sum(data["weeks"].values())
        dr = data["date_range"]
        assert dr["start"] <= dr["end"]
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_heatmap_weeks_are_sorted_ascending():
    """Week keys in the response must be in chronological order."""
    td = tempfile.mkdtemp()
    try:
        store = _make_store(td)
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/heatmap")

        assert resp.status_code == 200
        weeks = list(resp.json()["weeks"].keys())
        assert weeks == sorted(weeks)
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_heatmap_total_activity_matches_seeded_commits():
    """total_activity should equal the sum of all seeded commit counts."""
    td = tempfile.mkdtemp()
    try:
        # Alpha: 4 commits, Beta: 8 commits → 12 total
        store = _make_store(td, project_names=("Alpha", "Beta"))
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/heatmap")

        assert resp.status_code == 200
        assert resp.json()["total_activity"] == 12
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_heatmap_returns_404_when_no_projects():
    """Empty store → 404."""
    td = tempfile.mkdtemp()
    try:
        store = ProjectInsightsStore(db_path=os.path.join(td, "empty.db"), encryption_key=b"dev")
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/heatmap")

        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)
