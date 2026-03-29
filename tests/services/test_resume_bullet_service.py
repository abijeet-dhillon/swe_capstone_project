"""
Unit tests for src/services/resume_bullet_service.py

Tests cover:
  - _parse_bullets:  all response formats the LLM might return
  - _build_prompt:   correct context is included / missing data is safe
  - generate_resume_bullets_with_llm: happy path and error handling (mocked OpenAI)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.services.resume_bullet_service import (
    _build_prompt,
    _parse_bullets,
    generate_resume_bullets_with_llm,
)


# ---------------------------------------------------------------------------
# _parse_bullets
# ---------------------------------------------------------------------------

class TestParseBullets:

    def test_valid_json_array(self):
        raw = '["Built a REST API", "Improved performance by 40%", "Led team of 3"]'
        result = _parse_bullets(raw)
        assert result == ["Built a REST API", "Improved performance by 40%", "Led team of 3"]

    def test_json_array_truncated_to_three(self):
        raw = '["A", "B", "C", "D", "E"]'
        result = _parse_bullets(raw)
        assert len(result) == 3

    def test_json_inside_markdown_code_block(self):
        raw = '```json\n["Designed database", "Wrote tests", "Deployed on AWS"]\n```'
        result = _parse_bullets(raw)
        assert result == ["Designed database", "Wrote tests", "Deployed on AWS"]

    def test_json_inside_plain_code_block(self):
        raw = '```\n["A", "B", "C"]\n```'
        result = _parse_bullets(raw)
        assert result == ["A", "B", "C"]

    def test_numbered_list_fallback(self):
        raw = "1. Developed a full-stack web app\n2. Reduced load time by 30%\n3. Added unit tests"
        result = _parse_bullets(raw)
        assert len(result) == 3
        assert "Developed a full-stack web app" in result[0]

    def test_dash_list_fallback(self):
        raw = "- Built backend API\n- Wrote integration tests\n- Deployed to cloud"
        result = _parse_bullets(raw)
        assert len(result) == 3

    def test_bullet_point_fallback(self):
        raw = "• Engineered scalable service\n• Collaborated with team\n• Improved CI pipeline"
        result = _parse_bullets(raw)
        assert len(result) == 3

    def test_empty_string_returns_empty(self):
        assert _parse_bullets("") == []

    def test_invalid_json_falls_back_to_lines(self):
        raw = "not json at all\nDeveloped something cool using Python\nImproved system reliability"
        result = _parse_bullets(raw)
        # Should not raise; may return 0-2 items depending on line length filter
        assert isinstance(result, list)

    def test_strips_whitespace_from_bullets(self):
        raw = '["  Built API  ", "  Led team  ", "  Wrote docs  "]'
        result = _parse_bullets(raw)
        assert result[0] == "Built API"
        assert result[1] == "Led team"

    def test_filters_out_short_lines_in_fallback(self):
        raw = "- ok\n- Developed a comprehensive backend service using Python and FastAPI\n- hi"
        result = _parse_bullets(raw)
        # Only the long line passes the >15 char filter
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _build_prompt
# ---------------------------------------------------------------------------

class TestBuildPrompt:

    def _full_project_data(self):
        return {
            "project_metrics": {
                "languages": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "React"],
                "skills": ["REST API", "SQL", "Docker"],
                "total_lines": 8500,
                "total_files": 42,
                "has_tests": True,
                "has_documentation": True,
            },
            "git_analysis": {
                "total_commits": 120,
                "total_contributors": 3,
                "contributors": [
                    {
                        "commits": 80,
                        "activity_mix": {"feature": 0.6, "bugfix": 0.2, "refactor": 0.2},
                    },
                    {
                        "commits": 40,
                        "activity_mix": {"feature": 0.5, "docs": 0.3, "test": 0.2},
                    },
                ],
            },
        }

    def test_project_name_included(self):
        prompt = _build_prompt("MyProject", self._full_project_data(), [])
        assert "MyProject" in prompt

    def test_languages_included(self):
        prompt = _build_prompt("P", self._full_project_data(), [])
        assert "Python" in prompt
        assert "JavaScript" in prompt

    def test_frameworks_included(self):
        prompt = _build_prompt("P", self._full_project_data(), [])
        assert "FastAPI" in prompt
        assert "React" in prompt

    def test_scale_included(self):
        prompt = _build_prompt("P", self._full_project_data(), [])
        assert "8,500" in prompt

    def test_tests_and_docs_flags(self):
        prompt = _build_prompt("P", self._full_project_data(), [])
        assert "test" in prompt.lower()
        assert "documentation" in prompt.lower()

    def test_git_info_included(self):
        prompt = _build_prompt("P", self._full_project_data(), [])
        assert "120" in prompt  # commits

    def test_doc_summaries_included(self):
        summaries = [
            {"summary": "A web app for managing student grades with role-based access."},
            {"summary": "Supports CSV export and email notifications."},
        ]
        prompt = _build_prompt("P", self._full_project_data(), summaries)
        assert "student grades" in prompt
        assert "CSV export" in prompt

    def test_empty_project_data_does_not_raise(self):
        prompt = _build_prompt("EmptyProject", {}, [])
        assert "EmptyProject" in prompt

    def test_missing_metrics_does_not_raise(self):
        data = {"git_analysis": {"total_commits": 5, "total_contributors": 1, "contributors": []}}
        prompt = _build_prompt("P", data, [])
        assert isinstance(prompt, str)

    def test_doc_summaries_capped_at_three(self):
        summaries = [{"summary": f"Summary number {i} with enough words to pass."} for i in range(10)]
        prompt = _build_prompt("P", {}, summaries)
        # Only the first 3 summaries should appear
        assert "Summary number 3" not in prompt

    def test_short_doc_summaries_ignored(self):
        summaries = [{"summary": "too short"}]
        prompt = _build_prompt("P", {}, summaries)
        assert "too short" not in prompt

    def test_ends_with_generation_instruction(self):
        prompt = _build_prompt("P", {}, [])
        assert "JSON array" in prompt


# ---------------------------------------------------------------------------
# generate_resume_bullets_with_llm  (mocked OpenAI)
# ---------------------------------------------------------------------------

def _make_mock_openai_response(content: str):
    """Build a minimal mock that looks like an OpenAI ChatCompletion response."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


class TestGenerateResumeBulletsWithLlm:

    def _project_data(self):
        return {
            "project_metrics": {
                "languages": ["Python"],
                "frameworks": ["Django"],
                "skills": ["ORM", "REST"],
                "total_lines": 3000,
                "total_files": 20,
                "has_tests": True,
                "has_documentation": False,
            },
            "git_analysis": {
                "total_commits": 45,
                "total_contributors": 1,
                "contributors": [],
            },
        }

    def test_returns_bullets_on_success(self):
        bullets_json = '["Built Django app", "Wrote 45 unit tests", "Deployed to Heroku"]'
        mock_response = _make_mock_openai_response(bullets_json)

        mock_client_instance = MagicMock()
        mock_client_instance.client.chat.completions.create.return_value = mock_response

        with patch(
            "src.services.resume_bullet_service.OpenAIClient",
            return_value=mock_client_instance,
        ):
            result = generate_resume_bullets_with_llm("TestProject", self._project_data(), [])

        assert result == ["Built Django app", "Wrote 45 unit tests", "Deployed to Heroku"]

    def test_passes_doc_summaries_in_prompt(self):
        """Doc summaries should appear in the user message sent to OpenAI."""
        doc_summaries = [{"summary": "A grading system for university courses."}]

        # Capture the prompt via _build_prompt directly — no need to inspect mock internals
        prompt = _build_prompt("P", self._project_data(), doc_summaries)
        assert "grading system" in prompt

    def test_raises_on_openai_error(self):
        mock_client_instance = MagicMock()
        mock_client_instance.client.chat.completions.create.side_effect = RuntimeError("API down")

        with patch(
            "src.services.resume_bullet_service.OpenAIClient",
            return_value=mock_client_instance,
        ):
            with pytest.raises(RuntimeError, match="API down"):
                generate_resume_bullets_with_llm("P", self._project_data(), [])

    def test_raises_when_no_api_key(self):
        with patch(
            "src.services.resume_bullet_service.OpenAIClient",
            side_effect=ValueError("OpenAI API key not provided"),
        ):
            with pytest.raises(ValueError, match="OpenAI API key"):
                generate_resume_bullets_with_llm("P", self._project_data(), [])

    def test_handles_markdown_wrapped_json(self):
        wrapped = '```json\n["Led backend", "Improved DB speed", "Mentored juniors"]\n```'
        mock_response = _make_mock_openai_response(wrapped)

        mock_client_instance = MagicMock()
        mock_client_instance.client.chat.completions.create.return_value = mock_response

        with patch(
            "src.services.resume_bullet_service.OpenAIClient",
            return_value=mock_client_instance,
        ):
            result = generate_resume_bullets_with_llm("P", self._project_data(), [])

        assert result == ["Led backend", "Improved DB speed", "Mentored juniors"]
