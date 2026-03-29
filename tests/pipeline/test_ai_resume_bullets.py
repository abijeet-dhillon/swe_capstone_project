"""
Tests for the _generate_ai_resume_bullets orchestrator method.

Covers:
  - Bullets are saved for each eligible project when generation succeeds
  - A per-project failure is caught; other projects still get bullets
  - Projects whose name starts with '_' (misc files) are skipped
  - Returns early when the zip_hash cannot be resolved from the store
  - The full pipeline calls _generate_ai_resume_bullets only when use_llm=True
"""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ---------------------------------------------------------------------------
# Stub heavy optional dependencies so the orchestrator can be imported
# ---------------------------------------------------------------------------

def _stub(name):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)

for _mod in ("moviepy", "moviepy.editor", "whisper", "cv2", "pytesseract"):
    _stub(_mod)

if "pyzbar" not in sys.modules:
    _pyzbar = types.ModuleType("pyzbar")
    _pyzbar_pyzbar = types.ModuleType("pyzbar.pyzbar")
    _pyzbar_pyzbar.decode = lambda *a, **kw: []
    sys.modules["pyzbar"] = _pyzbar
    sys.modules["pyzbar.pyzbar"] = _pyzbar_pyzbar

for _sub in ("skimage", "skimage.feature", "skimage.filters", "skimage.measure", "skimage.color"):
    _stub(_sub)

sys.modules["skimage.color"].rgb2gray = lambda *a, **kw: None
sys.modules["skimage.feature"].graycomatrix = lambda *a, **kw: None
sys.modules["skimage.feature"].graycoprops = lambda *a, **kw: None

if not hasattr(sys.modules.get("moviepy.editor", types.ModuleType("x")), "VideoFileClip"):
    _editor = sys.modules.setdefault("moviepy.editor", types.ModuleType("moviepy.editor"))

    class _FakeClip:
        def __init__(self, *a, **kw):
            self.duration = 0
            self.fps = 0
            self.size = (0, 0)
            self.audio = None
        def close(self): pass

    _editor.VideoFileClip = _FakeClip

from src.pipeline.orchestrator import ArtifactPipeline  # noqa: E402

# The function is imported lazily *inside* _generate_ai_resume_bullets, so the
# correct patch target is the location where it is defined, not the orchestrator.
_BULLET_FN = "src.services.resume_bullet_service.generate_resume_bullets_with_llm"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(zip_hash="abc123", project_records=None):
    store = MagicMock()
    store.list_recent_zipfiles.return_value = [
        {"zip_path": "/uploads/test.zip", "zip_hash": zip_hash}
    ]
    store.list_projects_for_zip_detailed.return_value = project_records or [
        {"project_id": 1, "project_name": "ProjectA", "zip_hash": zip_hash},
        {"project_id": 2, "project_name": "ProjectB", "zip_hash": zip_hash},
    ]
    store.replace_resume_bullets.return_value = True
    return store


def _make_pipeline(store):
    pipeline = ArtifactPipeline(enable_insights=False)
    pipeline.insights_store = store
    return pipeline


PROJECT_RESULTS = {
    "ProjectA": {"project_metrics": {}, "git_analysis": {}},
    "ProjectB": {"project_metrics": {}, "git_analysis": {}},
}

LLM_SUMMARIES = {
    "ProjectA": [{"summary": "A web app for grade tracking."}],
    "ProjectB": [],
}


# ---------------------------------------------------------------------------
# Unit tests for _generate_ai_resume_bullets
# ---------------------------------------------------------------------------

class TestGenerateAiResumeBullets:

    def test_saves_bullets_for_each_project(self):
        store = _make_store()
        pipeline = _make_pipeline(store)

        bullets_a = ["Built API", "Wrote tests", "Deployed app"]
        bullets_b = ["Designed DB", "Led sprint", "Fixed bugs"]

        def fake_generate(project_name, project_data, doc_summaries):
            return bullets_a if project_name == "ProjectA" else bullets_b

        with patch(_BULLET_FN, side_effect=fake_generate):
            pipeline._generate_ai_resume_bullets(
                Path("/uploads/test.zip"), PROJECT_RESULTS, LLM_SUMMARIES
            )

        assert store.replace_resume_bullets.call_count == 2
        store.replace_resume_bullets.assert_any_call(1, bullets_a)
        store.replace_resume_bullets.assert_any_call(2, bullets_b)

    def test_skips_misc_file_projects(self):
        store = _make_store(
            project_records=[
                {"project_id": 1, "project_name": "RealProject", "zip_hash": "abc123"},
            ]
        )
        pipeline = _make_pipeline(store)

        results_with_misc = {
            "RealProject": {"project_metrics": {}, "git_analysis": {}},
            "_misc_files": {"project_metrics": {}, "git_analysis": {}},
        }

        with patch(_BULLET_FN, return_value=["Bullet 1", "Bullet 2", "Bullet 3"]):
            pipeline._generate_ai_resume_bullets(
                Path("/uploads/test.zip"), results_with_misc, {}
            )

        assert store.replace_resume_bullets.call_count == 1
        store.replace_resume_bullets.assert_called_once_with(
            1, ["Bullet 1", "Bullet 2", "Bullet 3"]
        )

    def test_per_project_failure_does_not_stop_others(self):
        store = _make_store()
        pipeline = _make_pipeline(store)

        def fake_generate(project_name, project_data, doc_summaries):
            if project_name == "ProjectA":
                raise RuntimeError("OpenAI timeout")
            return ["B1", "B2", "B3"]

        with patch(_BULLET_FN, side_effect=fake_generate):
            pipeline._generate_ai_resume_bullets(
                Path("/uploads/test.zip"), PROJECT_RESULTS, LLM_SUMMARIES
            )

        assert store.replace_resume_bullets.call_count == 1
        store.replace_resume_bullets.assert_called_once_with(2, ["B1", "B2", "B3"])

    def test_empty_bullets_not_saved(self):
        store = _make_store()
        pipeline = _make_pipeline(store)

        with patch(_BULLET_FN, return_value=[]):
            pipeline._generate_ai_resume_bullets(
                Path("/uploads/test.zip"), PROJECT_RESULTS, LLM_SUMMARIES
            )

        store.replace_resume_bullets.assert_not_called()

    def test_returns_early_when_zip_hash_not_found(self):
        store = _make_store()
        store.list_recent_zipfiles.return_value = [
            {"zip_path": "/uploads/other.zip", "zip_hash": "different_hash"}
        ]
        pipeline = _make_pipeline(store)

        with patch(_BULLET_FN) as mock_gen:
            pipeline._generate_ai_resume_bullets(
                Path("/uploads/test.zip"), PROJECT_RESULTS, LLM_SUMMARIES
            )

        mock_gen.assert_not_called()
        store.replace_resume_bullets.assert_not_called()

    def test_passes_doc_summaries_to_generator(self):
        store = _make_store(
            project_records=[
                {"project_id": 1, "project_name": "ProjectA", "zip_hash": "abc123"},
            ]
        )
        pipeline = _make_pipeline(store)
        captured = {}

        def fake_generate(project_name, project_data, doc_summaries):
            captured["summaries"] = doc_summaries
            return ["B1", "B2", "B3"]

        with patch(_BULLET_FN, side_effect=fake_generate):
            pipeline._generate_ai_resume_bullets(
                Path("/uploads/test.zip"),
                {"ProjectA": {"project_metrics": {}, "git_analysis": {}}},
                {"ProjectA": [{"summary": "A grade tracker."}]},
            )

        assert captured["summaries"] == [{"summary": "A grade tracker."}]

    def test_project_not_in_store_is_skipped(self):
        """Pipeline has a project the store doesn't know about — only the known one gets bullets."""
        store = _make_store(
            project_records=[
                {"project_id": 1, "project_name": "ProjectA", "zip_hash": "abc123"},
            ]
        )
        pipeline = _make_pipeline(store)

        with patch(_BULLET_FN, return_value=["B1", "B2", "B3"]):
            pipeline._generate_ai_resume_bullets(
                Path("/uploads/test.zip"), PROJECT_RESULTS, LLM_SUMMARIES
            )

        assert store.replace_resume_bullets.call_count == 1
        store.replace_resume_bullets.assert_called_once_with(1, ["B1", "B2", "B3"])


# ---------------------------------------------------------------------------
# Pipeline-level: _generate_ai_resume_bullets called iff use_llm=True
# ---------------------------------------------------------------------------

class TestPipelineCallsAiBullets:

    def _make_zip(self, tmp_path):
        import zipfile
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        (project_dir / "README.md").write_text("A project")
        zip_path = tmp_path / "proj.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(project_dir / "README.md", "proj/README.md")
        return zip_path

    def test_ai_bullets_called_when_use_llm_true(self, monkeypatch, tmp_path):
        zip_path = self._make_zip(tmp_path)
        pipeline = ArtifactPipeline(enable_insights=False)
        pipeline.insights_store = MagicMock()
        pipeline.insights_store.record_pipeline_run = MagicMock()

        called = {"ran": False}

        def fake_ai_bullets(zp, project_results, llm_summaries):
            called["ran"] = True

        monkeypatch.setattr(pipeline, "_analyze_categorized_files", lambda c: {})
        monkeypatch.setattr(pipeline, "_run_llm_summarization", lambda p: {})
        monkeypatch.setattr(pipeline, "_generate_ai_resume_bullets", fake_ai_bullets)

        pipeline.start(str(zip_path), use_llm=True)

        assert called["ran"] is True

    def test_ai_bullets_not_called_when_use_llm_false(self, monkeypatch, tmp_path):
        zip_path = self._make_zip(tmp_path)
        pipeline = ArtifactPipeline(enable_insights=False)

        called = {"ran": False}

        def fake_ai_bullets(*args, **kwargs):
            called["ran"] = True

        monkeypatch.setattr(pipeline, "_analyze_categorized_files", lambda c: {})
        monkeypatch.setattr(pipeline, "_generate_ai_resume_bullets", fake_ai_bullets)

        pipeline.start(str(zip_path), use_llm=False)

        assert called["ran"] is False

    def test_pipeline_completes_even_if_ai_bullets_raises(self, monkeypatch, tmp_path):
        zip_path = self._make_zip(tmp_path)
        pipeline = ArtifactPipeline(enable_insights=False)
        pipeline.insights_store = MagicMock()
        pipeline.insights_store.record_pipeline_run = MagicMock()

        def boom(*args, **kwargs):
            raise RuntimeError("AI completely broken")

        monkeypatch.setattr(pipeline, "_analyze_categorized_files", lambda c: {})
        monkeypatch.setattr(pipeline, "_run_llm_summarization", lambda p: {})
        monkeypatch.setattr(pipeline, "_generate_ai_resume_bullets", boom)

        result = pipeline.start(str(zip_path), use_llm=True)

        assert result is not None
        assert result.get("status") != "error"
