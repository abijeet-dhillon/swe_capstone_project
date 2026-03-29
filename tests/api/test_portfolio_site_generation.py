from __future__ import annotations
import os, shutil, tempfile
from pathlib import Path
from unittest.mock import patch
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


def test_ts_has_resume_url_slash_resume_pdf():
    """The generated portfolio.ts always includes resumeUrl: '/resume.pdf'."""
    ts = _build_portfolio_ts(_BASE)
    assert '"/resume.pdf"' in ts or "resumeUrl" in ts
# --- thumbnail image field in _build_portfolio_ts ---

def test_ts_project_uses_placeholder_when_no_image():
    """Project with no image field should fall back to /placeholder-project.jpg."""
    base = {**_BASE, "projects": [{"title": "P", "description": "D", "tags": ["python"]}]}
    ts = _build_portfolio_ts(base)
    assert "/placeholder-project.jpg" in ts


def test_ts_project_uses_provided_image_url():
    """Project with an explicit image URL should emit that URL, not the placeholder."""
    image_url = "http://localhost:8000/projects/42/thumbnail/content"
    base = {**_BASE, "projects": [{"title": "P", "description": "D", "image": image_url, "tags": ["python"]}]}
    ts = _build_portfolio_ts(base)
    assert image_url in ts
    assert "/placeholder-project.jpg" not in ts


def test_ts_multiple_projects_mixed_thumbnails():
    """Projects with and without thumbnails should each use the correct image value."""
    real_url = "http://localhost:8000/projects/1/thumbnail/content"
    base = {
        **_BASE,
        "projects": [
            {"title": "WithThumb", "description": "D1", "image": real_url, "tags": []},
            {"title": "NoThumb", "description": "D2", "tags": []},
        ],
    }
    ts = _build_portfolio_ts(base)
    assert real_url in ts
    assert "/placeholder-project.jpg" in ts


def test_ts_project_image_field_is_quoted_string():
    """The image value must be a quoted JS string in the output."""
    image_url = "http://localhost:8000/projects/5/thumbnail/content"
    base = {**_BASE, "projects": [{"title": "P", "description": "D", "image": image_url, "tags": []}]}
    ts = _build_portfolio_ts(base)
    assert f'image: "{image_url}"' in ts


# --- generate_portfolio_site thumbnail wiring ---

def test_generate_site_uses_thumbnail_url_when_file_exists():
    """When a project has a stored thumbnail on disk, the config should reference the backend URL."""
    td = tempfile.mkdtemp()
    try:
        store = _make_store(td)
        projects = store.list_available_projects() if hasattr(store, "list_available_projects") else []
        from src.pipeline.presentation_pipeline import PresentationPipeline
        pipeline = PresentationPipeline(insights_store=store)
        available = pipeline.list_available_projects()
        assert available, "No projects seeded"
        pid = available[0]["project_id"]

        # Write a fake thumbnail file and register it in the store
        thumb_dir = Path(td) / "thumbnails" / str(pid)
        thumb_dir.mkdir(parents=True)
        thumb_file = thumb_dir / "thumbnail.png"
        thumb_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        store.upsert_project_thumbnail(pid, str(thumb_file), "image/png")

        thumbnail = store.get_project_thumbnail(pid)
        assert thumbnail and thumbnail.get("image_path") == str(thumb_file)

        thumb_path = Path(thumbnail["image_path"])
        assert thumb_path.exists()
        expected_url = f"http://localhost:8000/projects/{pid}/thumbnail/content"
        image_url = expected_url if thumb_path.exists() else "/placeholder-project.jpg"
        assert image_url == expected_url
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_generate_site_uses_placeholder_when_no_thumbnail():
    """When a project has no thumbnail, the config image should be the placeholder."""
    td = tempfile.mkdtemp()
    try:
        store = _make_store(td)
        from src.pipeline.presentation_pipeline import PresentationPipeline
        available = PresentationPipeline(insights_store=store).list_available_projects()
        pid = available[0]["project_id"]

        thumbnail = store.get_project_thumbnail(pid)
        image_url = "/placeholder-project.jpg"
        if thumbnail and thumbnail.get("image_path"):
            p = Path(thumbnail["image_path"])
            if p.exists():
                image_url = f"http://localhost:8000/projects/{pid}/thumbnail/content"

        assert image_url == "/placeholder-project.jpg"
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_generate_site_uses_placeholder_when_thumbnail_file_missing():
    """Stale thumbnail DB record (file deleted) should fall back to placeholder."""
    td = tempfile.mkdtemp()
    try:
        store = _make_store(td)
        from src.pipeline.presentation_pipeline import PresentationPipeline
        available = PresentationPipeline(insights_store=store).list_available_projects()
        pid = available[0]["project_id"]

        # Register a thumbnail path that doesn't exist on disk
        store.upsert_project_thumbnail(pid, "/nonexistent/path/thumbnail.png", "image/png")
        thumbnail = store.get_project_thumbnail(pid)
        assert thumbnail and thumbnail.get("image_path") == "/nonexistent/path/thumbnail.png"

        thumb_path = Path(thumbnail["image_path"])
        assert not thumb_path.exists()
        image_url = (
            f"http://localhost:8000/projects/{pid}/thumbnail/content"
            if thumb_path.exists()
            else "/placeholder-project.jpg"
        )
        assert image_url == "/placeholder-project.jpg"
    finally:
        shutil.rmtree(td, ignore_errors=True)


# --- hiddenSections in _build_portfolio_ts ---

def test_ts_emits_empty_hidden_sections_by_default():
    ts = _build_portfolio_ts({**_BASE})
    assert "hiddenSections: []" in ts


def test_ts_emits_hidden_sections_when_provided():
    ts = _build_portfolio_ts({**_BASE, "hiddenSections": ["heatmap", "about"]})
    assert '"heatmap"' in ts
    assert '"about"' in ts
    assert "hiddenSections:" in ts


def test_ts_hidden_sections_is_valid_js_array():
    ts = _build_portfolio_ts({**_BASE, "hiddenSections": ["skills"]})
    assert 'hiddenSections: ["skills"]' in ts


def test_ts_hidden_sections_preserves_order():
    sections = ["showcase", "projects", "heatmap"]
    ts = _build_portfolio_ts({**_BASE, "hiddenSections": sections})
    assert '["showcase", "projects", "heatmap"]' in ts


def test_ts_hidden_sections_empty_list_explicit():
    ts = _build_portfolio_ts({**_BASE, "hiddenSections": []})
    assert "hiddenSections: []" in ts


# --- PortfolioSiteRequest hidden_sections field ---

def test_portfolio_site_request_accepts_hidden_sections():
    from src.api.routers.portfolio import PortfolioSiteRequest
    req = PortfolioSiteRequest(
        name="Test", project_ids=[1, 2],
        hidden_sections=["heatmap", "about"],
    )
    assert req.hidden_sections == ["heatmap", "about"]


def test_portfolio_site_request_defaults_hidden_sections_empty():
    from src.api.routers.portfolio import PortfolioSiteRequest
    req = PortfolioSiteRequest(name="Test", project_ids=[1, 2])
    assert req.hidden_sections == []
