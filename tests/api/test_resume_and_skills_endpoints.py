import os
import shutil
import sys
import tempfile
from pathlib import Path
import inspect
from unittest.mock import patch
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


def _seed_store(db_path: str) -> tuple[ProjectInsightsStore, list[int]]:
    store = ProjectInsightsStore(db_path=db_path, encryption_key=b"dev")
    payload = build_pipeline_payload(project_names=("ProjectAlpha", "ProjectBeta"), include_presentation=True)
    store.record_pipeline_run(os.path.join(os.path.dirname(db_path), "seed.zip"), payload)
    projects = PresentationPipeline(insights_store=store).list_available_projects()
    return store, [item["project_id"] for item in projects if item["project_name"] in {"ProjectAlpha", "ProjectBeta"}]


def test_skills_and_resume_endpoints():
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        store, project_ids = _seed_store(db_path)
        project_id = project_ids[0]
        role_store = ProjectRoleStore(db_path=db_path)
        config_manager = UserConfigManager(db_path=db_path)
        config_manager.create_config("default", "/tmp/demo.zip", False)
        config_manager.update_config(
            "default",
            name="Student Name",
            email="student@example.com",
            education=[
                {
                    "school": "University of Victoria",
                    "degree": "BSc Computer Science",
                    "location": "Victoria, BC",
                    "from": "Sep 2022",
                    "to": "May 2027",
                    "still_studying": True,
                }
            ],
            linkedin_url="https://linkedin.com/in/student",
            github_url="https://github.com/student",
        )

        app.dependency_overrides[deps.get_store] = lambda: store
        app.dependency_overrides[deps.get_role_store] = lambda: role_store
        app.dependency_overrides[deps.get_config_manager] = lambda: config_manager
        client = TestClient(app)

        # GET /skills
        resp = client.get("/skills")
        assert resp.status_code == 200
        skills = resp.json()
        assert isinstance(skills, list)
        assert all(isinstance(s, str) for s in skills)

        # GET /resume/{id}
        resp = client.get(f"/resume/{project_id}")
        assert resp.status_code == 200
        resume = resp.json()["resume_item"]
        assert isinstance(resume, dict)
        assert "bullets" in resume

        # POST /resume/generate (regenerate, returns resume)
        resp = client.post("/resume/generate", params={"project_id": project_id})
        assert resp.status_code == 200
        gen_resume = resp.json()["resume_item"]
        assert isinstance(gen_resume, dict)
        assert "bullets" in gen_resume

        def fake_generate(report, output_path, **_kwargs):
            Path(output_path).write_bytes(b"%PDF-1.4\n")
            return output_path

        from src.api.routers import resume as resume_router
        original = resume_router.generate_resume_pdf_artifact
        resume_router.generate_resume_pdf_artifact = fake_generate
        try:
            resp = client.post(
                "/resume/pdf",
                json={
                    "user_id": "default",
                    "project_ids": project_ids,
                },
            )
        finally:
            resume_router.generate_resume_pdf_artifact = original
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF-1.4")

        # POST /resume/{id}/edit (persist bullets)
        new_bullets = ["Defined API contracts", "Increased coverage"]
        resp = client.post(f"/resume/{project_id}/edit", json={"bullets": new_bullets})
        assert resp.status_code == 200
        edited = resp.json()["resume_item"]
        assert edited["bullets"] == new_bullets

        # POST /portfolio/generate (regenerate portfolio)
        resp = client.post("/portfolio/generate", params={"project_id": project_id})
        assert resp.status_code == 200
        portfolio = resp.json()["portfolio_item"]
        assert isinstance(portfolio, dict)
        assert "description" in portfolio

        # POST /portfolio/{id}/edit (persist fields)
        resp = client.post(
            f"/portfolio/{project_id}/edit",
            json={
                "tagline": "High-impact data project",
                "is_collaborative": True,
                "key_features": ["P1", "P2"],
            },
        )
        assert resp.status_code == 200
        updated_portfolio = resp.json()["portfolio_item"]
        assert updated_portfolio["tagline"] == "High-impact data project"
        assert updated_portfolio["is_collaborative"] is True
        assert updated_portfolio["key_features"] == ["P1", "P2"]
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


# --- _copy_to_portfolio_public ---

def test_copy_to_portfolio_public_writes_file():
    """Copies the PDF to the portfolio public directory."""
    from src.api.routers.resume import _copy_to_portfolio_public

    td = tempfile.mkdtemp()
    try:
        src = Path(td) / "source.pdf"
        src.write_bytes(b"%PDF-1.4 test")
        dest_dir = Path(td) / "portfolio" / "public"

        with patch("src.api.routers.resume._PORTFOLIO_PUBLIC_DIR", dest_dir), \
             patch("src.api.routers.resume._PORTFOLIO_RESUME_PATH", dest_dir / "resume.pdf"):
            _copy_to_portfolio_public(src)

        assert (dest_dir / "resume.pdf").exists()
        assert (dest_dir / "resume.pdf").read_bytes() == b"%PDF-1.4 test"
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_copy_to_portfolio_public_overwrites_previous():
    """A second copy replaces the previous resume.pdf."""
    from src.api.routers.resume import _copy_to_portfolio_public

    td = tempfile.mkdtemp()
    try:
        dest_dir = Path(td) / "portfolio" / "public"
        dest_dir.mkdir(parents=True)
        (dest_dir / "resume.pdf").write_bytes(b"old content")

        src = Path(td) / "new.pdf"
        src.write_bytes(b"%PDF-1.4 new")

        with patch("src.api.routers.resume._PORTFOLIO_PUBLIC_DIR", dest_dir), \
             patch("src.api.routers.resume._PORTFOLIO_RESUME_PATH", dest_dir / "resume.pdf"):
            _copy_to_portfolio_public(src)

        assert (dest_dir / "resume.pdf").read_bytes() == b"%PDF-1.4 new"
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_pdf_bundle_copies_to_portfolio_public():
    """POST /resume/pdf copies the compiled PDF to the portfolio public directory."""
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        store, project_ids = _seed_store(db_path)
        role_store = ProjectRoleStore(db_path=db_path)
        app.dependency_overrides[deps.get_store] = lambda: store
        app.dependency_overrides[deps.get_role_store] = lambda: role_store
        client = TestClient(app)

        dest_dir = Path(td) / "portfolio" / "public"
        copied: list[bytes] = []

        def fake_generate(report, output_path, **_):
            Path(output_path).write_bytes(b"%PDF-1.4 bundle")
            return Path(output_path)

        def fake_copy(src: Path) -> None:
            copied.append(src.read_bytes())

        from src.api.routers import resume as resume_router
        original_gen = resume_router.generate_resume_pdf_artifact
        original_copy = resume_router._copy_to_portfolio_public
        resume_router.generate_resume_pdf_artifact = fake_generate
        resume_router._copy_to_portfolio_public = fake_copy
        try:
            resp = client.post(
                "/resume/pdf",
                json={
                    "resume_owner_name": "Test User",
                    "project_ids": project_ids,
                },
            )
        finally:
            resume_router.generate_resume_pdf_artifact = original_gen
            resume_router._copy_to_portfolio_public = original_copy
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert len(copied) == 1, "Expected _copy_to_portfolio_public to be called once"
        assert copied[0] == b"%PDF-1.4 bundle"
        detail = resp.json()["detail"]
        assert "missing_fields" in detail
        assert set(detail["missing_fields"]) >= {"name", "contact.email", "education"}
    finally:
        shutil.rmtree(td, ignore_errors=True)
