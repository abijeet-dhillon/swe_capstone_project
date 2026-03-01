import inspect
import os
import shutil
import sys
import tempfile
import types
import zipfile
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.api import deps
from src.api.app import app
from src.config.config_manager import UserConfigManager
from src.insights.storage import ProjectInsightsStore
from tests.insights.utils import build_pipeline_payload

if "app" not in inspect.signature(httpx.Client.__init__).parameters:
    _orig_httpx_init = httpx.Client.__init__

    def _patched_httpx_init(self, *args, **kwargs):
        kwargs.pop("app", None)
        return _orig_httpx_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_httpx_init


def _upload_result():
    payload = build_pipeline_payload(project_names=("ProjectAlpha", "ProjectBeta"), include_presentation=True)
    alpha, beta = payload["projects"]["ProjectAlpha"], payload["projects"]["ProjectBeta"]
    alpha["project_metrics"].update({"skills": ["Python", "FastAPI"], "frameworks": ["FastAPI"], "languages": ["Python"], "total_lines": 120, "duration_days": 120, "duration_end": "2025-12-01"})
    beta["project_metrics"].update({"skills": ["React", "TypeScript"], "frameworks": ["React"], "languages": ["TypeScript"], "total_lines": 320, "duration_days": 30, "duration_end": "2026-01-15"})
    alpha["portfolio_item"].update(alpha["project_metrics"])
    beta["portfolio_item"].update(beta["project_metrics"])
    alpha["git_analysis"] = {"total_commits": 8, "total_contributors": 2, "contributors": [{"name": "Alice", "commits": 6}, {"name": "Bob", "commits": 2}], "activity_mix": {"code": 8, "test": 1, "doc": 1}, "last_commit_at": "2025-12-01", "duration_days": 120}
    beta["git_analysis"] = {"total_commits": 3, "total_contributors": 1, "contributors": [{"name": "Solo", "commits": 3}], "activity_mix": {"code": 3, "test": 0, "doc": 0}, "last_commit_at": "2026-01-15", "duration_days": 30}
    payload["project_ranking"] = {
        "ranked_projects": [{"rank": 1, "name": "ProjectAlpha", "score": 10.0}, {"rank": 2, "name": "ProjectBeta", "score": 9.0}],
        "top_summaries": [
            {"rank": 1, "name": "ProjectAlpha", "criteria": "score", "summary": "Alpha summary", "metrics": {"commits": 8, "loc": 120, "recency_days": 0, "languages": ["Python"], "duration_days": 120}},
            {"rank": 2, "name": "ProjectBeta", "criteria": "score", "summary": "Beta summary", "metrics": {"commits": 3, "loc": 320, "recency_days": 0, "languages": ["TypeScript"], "duration_days": 30}},
        ],
        "total_projects_ranked": 2,
    }
    payload["chronological_skills"] = {
        "timeline": [
            {"file": "alpha/app.py", "timestamp": "2025-12-01T10:00:00", "category": "code", "skills": ["Python"], "metadata": {}},
            {"file": "beta/app.ts", "timestamp": "2026-01-15T09:30:00", "category": "code", "skills": ["TypeScript"], "metadata": {}},
        ],
        "total_events": 2,
        "categories": ["code"],
    }
    return payload


@pytest.fixture()
def upload_env():
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        store = ProjectInsightsStore(db_path=db_path, encryption_key=b"dev")
        manager = UserConfigManager(db_path=db_path)
        zip_path = os.path.join(td, "demo.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("hello.txt", "hello")
        manager.create_config("uploader", zip_path, llm_consent=False, llm_consent_asked=True, data_access_consent=True)
        app.dependency_overrides[deps.get_store] = lambda: store
        app.dependency_overrides[deps.get_config_manager] = lambda: manager
        dummy = types.ModuleType("src.pipeline.orchestrator")

        class _DummyPipeline:
            def __init__(self, insights_store=None):
                self.insights_store = insights_store

            def start(self, zip_path, use_llm=False, data_access_consent=True, prompt_project_names=False, git_identifier=None):
                result = _upload_result()
                self.insights_store.record_pipeline_run(zip_path, result)
                return result

        dummy.ArtifactPipeline = _DummyPipeline
        sys.modules["src.pipeline.orchestrator"] = dummy
        yield {"store": store, "zip_path": zip_path, "client": TestClient(app)}
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_upload_defaults_to_show_everything(upload_env):
    data = upload_env["client"].post("/projects/upload", json={"user_id": "uploader", "zip_path": upload_env["zip_path"]}).json()
    assert data["projects"] == ["ProjectAlpha", "ProjectBeta"]
    assert data["representation"]["sections"] == ["projects", "ranking", "chronology", "skills", "attributes", "showcase"]
    assert set(data["represented_output"]) == set(data["representation"]["sections"])
    assert upload_env["store"].load_run_representation(data["ingest_id"]) == data["representation"]


def test_upload_with_representation_overrides(upload_env):
    response = upload_env["client"].post(
        "/projects/upload",
        json={
            "user_id": "uploader",
            "zip_path": upload_env["zip_path"],
            "representation": {"sections": ["ranking", "skills", "showcase"], "ranking": {"criteria": "loc", "n": 1}, "skills": {"highlight": ["TypeScript"], "suppress": ["Python"]}, "showcase": {"selected_projects": ["ProjectBeta"]}},
        },
    )
    data = response.json()
    assert response.status_code == 200
    assert set(data["represented_output"]) == {"ranking", "skills", "showcase"}
    assert data["represented_output"]["ranking"]["items"][0]["name"] == "ProjectBeta"
    assert data["represented_output"]["skills"]["skills"] == ["TypeScript", "FastAPI", "React"]
    assert [item["project_name"] for item in data["represented_output"]["showcase"]["projects"]] == ["ProjectBeta"]
    assert upload_env["store"].load_run_representation(data["ingest_id"]) == data["representation"]


def test_upload_skills_wrapper_returns_only_skills(upload_env):
    response = upload_env["client"].post("/projects/upload/skills", json={"user_id": "uploader", "zip_path": upload_env["zip_path"], "representation": {"skills": {"highlight": ["Python"]}}})
    data = response.json()
    assert response.status_code == 200
    assert data["representation"]["sections"] == ["skills"]
    assert list(data["represented_output"]) == ["skills"]
    assert data["represented_output"]["skills"]["highlighted"] == ["Python"]


@pytest.mark.parametrize("representation", [{"sections": ["invalid"]}, {"sections": ["ranking"], "ranking": {"criteria": "invalid"}}])
def test_upload_rejects_invalid_representation(upload_env, representation):
    assert upload_env["client"].post("/projects/upload", json={"user_id": "uploader", "zip_path": upload_env["zip_path"], "representation": representation}).status_code == 422


def test_upload_representation_does_not_change_analysis(upload_env):
    data = upload_env["client"].post("/projects/upload", json={"user_id": "uploader", "zip_path": upload_env["zip_path"], "representation": {"sections": ["skills"]}}).json()
    report = upload_env["store"].load_zip_report(data["zip_hash"])
    assert set(data["represented_output"]) == {"skills"}
    assert set(report["projects"]) == {"ProjectAlpha", "ProjectBeta"}
    assert report["projects"]["ProjectAlpha"]["project_metrics"]["total_lines"] == 120
    assert report["projects"]["ProjectBeta"]["project_metrics"]["total_lines"] == 320
    assert "project_ranking" in report["global_insights"] and "chronological_skills" in report["global_insights"]
