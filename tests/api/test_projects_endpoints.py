import inspect
import os
import shutil
import sys
import tempfile
import zipfile
import inspect
from pathlib import Path
import httpx

import httpx
from fastapi.testclient import TestClient

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.api import deps
from src.api.app import app
from src.config.config_manager import UserConfigManager
from src.insights.storage import ProjectInsightsStore
from src.insights.user_role_store import ProjectRoleStore
from src.pipeline.presentation_pipeline import PresentationPipeline
from tests.insights.utils import build_pipeline_payload

# Compatibility shim: older httpx versions don't accept the 'app' kwarg used by Starlette's TestClient
if "app" not in inspect.signature(httpx.Client.__init__).parameters:
    _orig_httpx_init = httpx.Client.__init__

    def _patched_httpx_init(self, *args, **kwargs):
        kwargs.pop("app", None)
        return _orig_httpx_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_httpx_init


def _seed_store(db_path: str) -> tuple[ProjectInsightsStore, str, int]:
    store = ProjectInsightsStore(db_path=db_path, encryption_key=b"dev")
    payload = build_pipeline_payload()
    store.record_pipeline_run(os.path.join(os.path.dirname(db_path), "seed.zip"), payload)
    zip_hash = store.list_recent_zipfiles(limit=1)[0]["zip_hash"]
    projects = PresentationPipeline(insights_store=store).list_available_projects()
    project_id = next(item["project_id"] for item in projects if item["project_name"] == "ProjectAlpha")
    return store, zip_hash, project_id


def test_projects_list_and_detail_and_portfolio():
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        store, zip_hash, project_id = _seed_store(db_path)
        role_store = ProjectRoleStore(db_path=db_path)
        role_store.set_user_role(zip_hash, "ProjectAlpha", "Lead Developer")

        app.dependency_overrides[deps.get_store] = lambda: store
        app.dependency_overrides[deps.get_role_store] = lambda: role_store

        client = TestClient(app)

        response = client.get("/projects")
        assert response.status_code == 200
        items = response.json()
        assert any(item["project_id"] == project_id for item in items)

        response = client.get(f"/projects/{project_id}")
        assert response.status_code == 200
        payload = response.json()
        assert payload["project_id"] == project_id
        assert payload["user_role"] == "Lead Developer"

        response = client.get(f"/portfolio/{project_id}")
        assert response.status_code == 200
        portfolio = response.json()
        assert portfolio["project_id"] == project_id
        assert portfolio["project_title"] == payload["project_name"]
        assert portfolio["user_role"] == "Lead Developer"
        assert "key_skills" in portfolio
        assert "key_metrics" in portfolio

        response = client.get(f"/resume/{project_id}")
        assert response.status_code == 200
        assert response.json()["user_role"] == "Lead Developer"
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_projects_upload_triggers_pipeline(monkeypatch):
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        store = ProjectInsightsStore(db_path=db_path, encryption_key=b"dev")
        manager = UserConfigManager(db_path=db_path)

        zip_path = os.path.join(td, "demo.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("hello.txt", "hello")

        manager.create_config(
            "uploader",
            zip_path,
            llm_consent=False,
            llm_consent_asked=True,
            data_access_consent=True,
        )

        app.dependency_overrides[deps.get_store] = lambda: store
        app.dependency_overrides[deps.get_config_manager] = lambda: manager

        import types, sys as _sys

        dummy_module = types.ModuleType("src.pipeline.orchestrator")
        report_json_path = Path("reports") / "report_upload_test.json"
        report_pdf_path = report_json_path.with_suffix(".pdf")

        class _DummyPipeline:
            def __init__(self, insights_store=None):
                self.insights_store = insights_store

            def start(self, zip_path, use_llm=False, data_access_consent=True, prompt_project_names=False, git_identifier=None):
                result = build_pipeline_payload()
                self.insights_store.record_pipeline_run(zip_path, result)
                report_json_path.parent.mkdir(exist_ok=True)
                report_json_path.write_text("{}", encoding="utf-8")
                report_pdf_path.write_bytes(b"%PDF-1.4\n")
                result["artifacts"] = {
                    "json_report_path": str(report_json_path),
                    "resume_pdf_path": str(report_pdf_path),
                }
                return result

        dummy_module.ArtifactPipeline = _DummyPipeline
        _sys.modules["src.pipeline.orchestrator"] = dummy_module

        client = TestClient(app)
        response = client.post("/projects/upload", json={"user_id": "uploader", "zip_path": zip_path})

        assert response.status_code == 200
        data = response.json()
        assert data["zip_hash"]
        assert data["projects"]
        assert data["resume_pdf_path"] == str(report_pdf_path)
    finally:
        app.dependency_overrides.clear()
        report = Path("reports")
        (report / "report_upload_test.json").unlink(missing_ok=True)
        (report / "report_upload_test.pdf").unlink(missing_ok=True)
        shutil.rmtree(td, ignore_errors=True)


def test_project_role_set_get_and_validation():
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        store, _, project_id = _seed_store(db_path)
        role_store = ProjectRoleStore(db_path=db_path)

        app.dependency_overrides[deps.get_store] = lambda: store
        app.dependency_overrides[deps.get_role_store] = lambda: role_store
        client = TestClient(app)

        response = client.put(f"/projects/{project_id}/role", json={"role": "  Technical Lead  "})
        assert response.status_code == 200
        assert response.json()["user_role"] == "Technical Lead"

        response = client.get(f"/projects/{project_id}/role")
        assert response.status_code == 200
        assert response.json()["user_role"] == "Technical Lead"

        response = client.get(f"/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["user_role"] == "Technical Lead"

        response = client.get(f"/portfolio/{project_id}")
        assert response.status_code == 200
        assert response.json()["user_role"] == "Technical Lead"

        response = client.get(f"/resume/{project_id}")
        assert response.status_code == 200
        assert response.json()["user_role"] == "Technical Lead"

        response = client.put(f"/projects/{project_id}/role", json={"role": "   "})
        assert response.status_code == 422

        response = client.put("/projects/999999/role", json={"role": "Lead"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_project_thumbnail_upload_and_errors():
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        store, _, project_id = _seed_store(db_path)
        thumbnails_root = Path(td) / "thumbnails"
        max_bytes = 32

        app.dependency_overrides[deps.get_store] = lambda: store
        app.dependency_overrides[deps.get_thumbnail_root] = lambda: thumbnails_root
        app.dependency_overrides[deps.get_thumbnail_max_bytes] = lambda: max_bytes
        client = TestClient(app)

        png_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * 12
        files = {"file": ("thumb.png", png_bytes, "image/png")}
        response = client.post(f"/projects/{project_id}/thumbnail", files=files)
        assert response.status_code == 200
        payload = response.json()
        assert payload["project_id"] == project_id
        assert payload["size_bytes"] == len(png_bytes)
        assert Path(payload["thumbnail_path"]).exists()

        response = client.get(f"/projects/{project_id}/thumbnail")
        assert response.status_code == 200
        thumb = response.json()
        assert thumb["thumbnail_path"].endswith("thumbnail.png")
        assert thumb["thumbnail_url"] == f"/projects/{project_id}/thumbnail/content"

        response = client.get(f"/projects/{project_id}/thumbnail/content")
        assert response.status_code == 200
        assert response.content == png_bytes

        response = client.get(f"/portfolio/{project_id}")
        assert response.status_code == 200
        assert response.json()["thumbnail_url"] == f"/projects/{project_id}/thumbnail/content"

        bad_files = {"file": ("bad.txt", b"hello", "text/plain")}
        response = client.post(f"/projects/{project_id}/thumbnail", files=bad_files)
        assert response.status_code == 400
        assert "Invalid file type" in response.text

        too_big = {"file": ("big.jpg", b"x" * (max_bytes + 1), "image/jpeg")}
        response = client.post(f"/projects/{project_id}/thumbnail", files=too_big)
        assert response.status_code == 400
        assert "File too large" in response.text

        response = client.post("/projects/999999/thumbnail", files=files)
        assert response.status_code == 404

        response = client.delete(f"/projects/{project_id}/thumbnail")
        assert response.status_code == 200
        response = client.get(f"/projects/{project_id}/thumbnail")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)
