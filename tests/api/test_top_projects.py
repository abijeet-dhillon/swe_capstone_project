"""
Tests for GET /portfolio/top — top-N projects showcase endpoint.

Covers:
- Returns ranked projects with evolution data (normal case)
- Respects the `limit` query parameter
- Public mode strips customization fields
- Private mode (default) includes customization fields
- Returns 404 when no projects exist in the store
"""
from __future__ import annotations

import os
import shutil
import tempfile

from fastapi.testclient import TestClient

from src.api import deps
from src.api.app import app
from src.insights.storage import ProjectInsightsStore
from src.pipeline.presentation_pipeline import PresentationPipeline
from tests.insights.utils import build_pipeline_payload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_store(db_path: str, project_names=("Alpha", "Beta", "Gamma")) -> tuple[ProjectInsightsStore, list[int]]:
    """Seed a fresh DB with synthetic projects; return store + ordered project IDs."""
    store = ProjectInsightsStore(db_path=db_path, encryption_key=b"dev")
    payload = build_pipeline_payload(project_names=project_names, include_presentation=True)
    # Give each project distinct commit counts so ranking is deterministic
    for idx, name in enumerate(project_names):
        payload["projects"][name]["git_analysis"] = {"total_commits": (idx + 1) * 10}
        metrics = payload["projects"][name].get("project_metrics") or {}
        metrics["total_commits"] = (idx + 1) * 10
        metrics["total_lines"] = (idx + 1) * 100
        payload["projects"][name]["project_metrics"] = metrics
    store.record_pipeline_run(os.path.join(os.path.dirname(db_path), "seed.zip"), payload)
    pipeline = PresentationPipeline(insights_store=store)
    projects = pipeline.list_available_projects()
    ids = [p["project_id"] for p in projects if p["project_name"] in project_names]
    return store, ids


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_top_projects_returns_ranked_list_with_evolution():
    """Returns top-3 projects each with rank, score, key_metrics, and evolution block."""
    td = tempfile.mkdtemp()
    try:
        store, _ = _seed_store(os.path.join(td, "app.db"))
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/top")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert data["limit"] == 3
        assert len(data["projects"]) == 3

        first = data["projects"][0]
        assert first["rank"] == 1
        assert "score" in first
        assert "key_metrics" in first
        evolution = first["evolution"]
        assert "total_commits" in evolution
        assert "duration_days" in evolution
        assert "first_commit_at" in evolution
        assert "last_commit_at" in evolution
        assert "contributors" in evolution
        assert "activity_mix" in evolution
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_top_projects_limit_param_respected():
    """limit=1 returns exactly one project."""
    td = tempfile.mkdtemp()
    try:
        store, _ = _seed_store(os.path.join(td, "app.db"))
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/top?limit=1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["limit"] == 1
        assert len(data["projects"]) == 1
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_top_projects_public_mode_omits_customization_fields():
    """mode=public strips editable fields (tagline, key_features, etc.)."""
    td = tempfile.mkdtemp()
    try:
        store, _ = _seed_store(os.path.join(td, "app.db"))
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/top?mode=public")

        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "public"
        for project in data["projects"]:
            assert "tagline" not in project
            assert "key_features" not in project
            assert "is_collaborative" not in project
            assert "summary" in project  # read-only summary is kept
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_top_projects_private_mode_includes_customization_fields():
    """mode=private (default) includes all customization fields."""
    td = tempfile.mkdtemp()
    try:
        store, _ = _seed_store(os.path.join(td, "app.db"))
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/top?mode=private")

        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "private"
        for project in data["projects"]:
            assert "tagline" in project
            assert "key_features" in project
            assert "is_collaborative" in project
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_top_projects_returns_404_when_no_projects():
    """Returns 404 when the store is empty."""
    td = tempfile.mkdtemp()
    try:
        store = ProjectInsightsStore(db_path=os.path.join(td, "empty.db"), encryption_key=b"dev")
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/top")

        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_top_projects_ordered_highest_score_first():
    """Projects are returned in descending score order (rank 1 has the highest score)."""
    td = tempfile.mkdtemp()
    try:
        store, _ = _seed_store(os.path.join(td, "app.db"))
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)

        resp = client.get("/portfolio/top?limit=3")

        assert resp.status_code == 200
        projects = resp.json()["projects"]
        scores = [p["score"] for p in projects]
        assert scores == sorted(scores, reverse=True), "Projects must be ordered highest score first"
        ranks = [p["rank"] for p in projects]
        assert ranks == list(range(1, len(ranks) + 1)), "Ranks must be sequential starting at 1"
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)