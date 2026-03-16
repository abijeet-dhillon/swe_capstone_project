import inspect
import os
import shutil
import sys
import tempfile
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.api import deps
from src.api.app import app
from src.insights.storage import ProjectInsightsStore
from src.pipeline.presentation_pipeline import PresentationPipeline
from tests.insights.utils import build_pipeline_payload

# Compatibility shim: older httpx versions don't accept the 'app' kwarg used by Starlette's TestClient
if "app" not in inspect.signature(httpx.Client.__init__).parameters:
    _orig_httpx_init = httpx.Client.__init__

    def _patched_httpx_init(self, *args, **kwargs):
        kwargs.pop("app", None)
        return _orig_httpx_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_httpx_init


def _seed_store(db_path: str) -> tuple[ProjectInsightsStore, int]:
    store = ProjectInsightsStore(db_path=db_path, encryption_key=b"dev")
    payload = build_pipeline_payload(project_names=("ProjectAlpha",), include_presentation=True)
    payload["projects"]["ProjectAlpha"]["project_metrics"]["skills"] = []
    payload["chronological_skills"] = {
        "timeline": [
            {
                "file": "alpha/a.py",
                "timestamp": "2025-12-30T10:00:00",
                "category": "code",
                "skills": ["python"],
                "metadata": {},
            },
            {
                "file": "alpha/b.py",
                "timestamp": "2026-01-04T11:30:00",
                "category": "code",
                "skills": ["fastapi"],
                "metadata": {},
            },
            {
                "file": "alpha/c.md",
                "timestamp": "2026-08-20T09:15:00",
                "category": "text",
                "skills": ["writing"],
                "metadata": {},
            },
        ],
        "total_events": 3,
        "categories": ["code", "text"],
    }
    store.record_pipeline_run(os.path.join(os.path.dirname(db_path), "seed.zip"), payload)
    projects = PresentationPipeline(insights_store=store).list_available_projects()
    project_id = next(item["project_id"] for item in projects if item["project_name"] == "ProjectAlpha")
    return store, project_id


@pytest.fixture()
def skills_client():
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        store, project_id = _seed_store(db_path)
        app.dependency_overrides[deps.get_store] = lambda: store
        client = TestClient(app)
        yield client, project_id
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_add_skills_normalizes_and_dedupes(skills_client):
    client, project_id = skills_client
    response = client.post(
        "/skills/add",
        json={"project_id": project_id, "skills": [" Python ", "python", "FASTAPI", ""]},
    )
    assert response.status_code == 200
    assert response.json() == {"project_id": project_id, "skills": ["python", "fastapi"]}


def test_remove_skills_case_insensitive(skills_client):
    client, project_id = skills_client
    client.post("/skills/add", json={"project_id": project_id, "skills": ["python", "fastapi"]})

    response = client.post(
        "/skills/remove",
        json={"project_id": project_id, "skills": ["PYTHON"]},
    )
    assert response.status_code == 200
    assert response.json() == {"project_id": project_id, "skills": ["fastapi"]}


def test_edit_skill_old_to_new_and_old_missing_noop(skills_client):
    client, project_id = skills_client
    client.post("/skills/add", json={"project_id": project_id, "skills": ["fastapi"]})

    replace_response = client.post(
        "/skills/edit",
        json={"project_id": project_id, "old": "fastapi", "new": "backend"},
    )
    assert replace_response.status_code == 200
    assert replace_response.json() == {"project_id": project_id, "skills": ["backend"]}

    noop_response = client.post(
        "/skills/edit",
        json={"project_id": project_id, "old": "missing", "new": "newskill"},
    )
    assert noop_response.status_code == 200
    assert noop_response.json() == {"project_id": project_id, "skills": ["backend"]}


def test_edit_replace_list(skills_client):
    client, project_id = skills_client
    response = client.post(
        "/skills/edit",
        json={"project_id": project_id, "skills": [" GraphQL ", "graphql", "API "]},
    )
    assert response.status_code == 200
    assert response.json() == {"project_id": project_id, "skills": ["graphql", "api"]}


def test_get_project_skills_returns_expected_list(skills_client):
    client, project_id = skills_client
    client.post("/skills/add", json={"project_id": project_id, "skills": ["python", "fastapi"]})

    response = client.get(f"/skills/{project_id}")
    assert response.status_code == 200
    assert response.json() == {"project_id": project_id, "skills": ["python", "fastapi"]}


def test_get_skills_year_filters_timeline(skills_client):
    client, _ = skills_client
    response = client.get("/skills/year", params={"year": 2026})
    assert response.status_code == 200
    payload = response.json()
    assert payload["year"] == 2026
    assert len(payload["timeline"]) == 2
    assert all(event["timestamp"].startswith("2026") for event in payload["timeline"])


def test_unknown_project_returns_404(skills_client):
    client, _ = skills_client
    response = client.get("/skills/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_year_validation_422(skills_client):
    client, _ = skills_client
    response = client.get("/skills/year", params={"year": 26})
    assert response.status_code == 422


def test_skill_mutations_persist_to_chronological_timeline(skills_client):
    client, project_id = skills_client

    add_response = client.post(
        "/skills/add",
        json={"project_id": project_id, "skills": ["graphql"], "month": 2, "year": 2027},
    )
    assert add_response.status_code == 200
    assert "graphql" in add_response.json()["skills"]

    after_add = client.get(f"/chronological/skills/{project_id}")
    assert after_add.status_code == 200
    add_timeline = after_add.json()["timeline"]
    assert any("graphql" in item.get("skills", []) for item in add_timeline)
    assert any(
        "graphql" in item.get("skills", []) and str(item.get("timestamp", "")).startswith("2027-02-01")
        for item in add_timeline
    )

    edit_response = client.post(
        "/skills/edit",
        json={"project_id": project_id, "old": "graphql", "new": "rust", "month": 3, "year": 2028},
    )
    assert edit_response.status_code == 200
    assert "graphql" not in edit_response.json()["skills"]
    assert "rust" in edit_response.json()["skills"]

    after_edit = client.get(f"/chronological/skills/{project_id}")
    assert after_edit.status_code == 200
    edit_timeline = after_edit.json()["timeline"]
    assert all("graphql" not in item.get("skills", []) for item in edit_timeline)
    assert any("rust" in item.get("skills", []) for item in edit_timeline)
    assert any(
        "rust" in item.get("skills", []) and str(item.get("timestamp", "")).startswith("2028-03-01")
        for item in edit_timeline
    )

    remove_response = client.post(
        "/skills/remove",
        json={"project_id": project_id, "skills": ["rust"]},
    )
    assert remove_response.status_code == 200
    assert "rust" not in remove_response.json()["skills"]

    after_remove = client.get(f"/chronological/skills/{project_id}")
    assert after_remove.status_code == 404


def test_month_year_must_be_provided_together(skills_client):
    client, project_id = skills_client
    response = client.post(
        "/skills/add",
        json={"project_id": project_id, "skills": ["python"], "month": 5},
    )
    assert response.status_code == 400
    assert "month" in response.json()["detail"].lower()


def test_empty_override_does_not_fallback_to_base_chronology(skills_client):
    client, project_id = skills_client
    clear_response = client.post(
        "/skills/edit",
        json={"project_id": project_id, "skills": []},
    )
    assert clear_response.status_code == 200
    assert clear_response.json() == {"project_id": project_id, "skills": []}

    timeline_response = client.get(f"/chronological/skills/{project_id}")
    assert timeline_response.status_code == 404
