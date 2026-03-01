"""Tests for LinkedIn API endpoints"""
from __future__ import annotations

import inspect

import httpx
import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.insights.storage import ProjectInsightsStore

if "app" not in inspect.signature(httpx.Client.__init__).parameters:
    _orig_httpx_init = httpx.Client.__init__

    def _patched_httpx_init(self, *args, **kwargs):
        kwargs.pop("app", None)
        return _orig_httpx_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_httpx_init

client = TestClient(app)


@pytest.fixture
def mock_project_data():
    """Mock project data with portfolio item"""
    return {
        "project_name": "Test API Project",
        "portfolio_item": {
            "project_name": "Test API Project",
            "tagline": "A test project for API",
            "description": "This is a test project to validate LinkedIn API endpoints.",
            "languages": ["Python", "JavaScript"],
            "frameworks": ["FastAPI", "React"],
            "skills": ["API Design", "Testing"],
            "is_collaborative": False,
            "total_commits": 100,
            "total_lines": 2000,
            "total_files": 30,
        },
    }


def test_get_linkedin_preview_success(monkeypatch, mock_project_data):
    """Test successful LinkedIn preview generation"""

    def mock_load_project_insight_by_id(self, project_id):
        if project_id == 1:
            return mock_project_data
        return None

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    response = client.get("/linkedin/preview/1")
    assert response.status_code == 200

    data = response.json()
    assert "text" in data
    assert "char_count" in data
    assert "exceeds_limit" in data
    assert "hashtags" in data
    assert "preview" in data
    assert data["project_id"] == 1
    assert data["project_name"] == "Test API Project"
    assert data["char_count"] > 0
    assert not data["exceeds_limit"]


def test_get_linkedin_preview_not_found(monkeypatch):
    """Test 404 when project not found"""

    def mock_load_project_insight_by_id(self, project_id):
        return None

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    response = client.get("/linkedin/preview/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_linkedin_preview_no_portfolio(monkeypatch):
    """Test 404 when portfolio item not generated"""

    def mock_load_project_insight_by_id(self, project_id):
        return {"project_name": "Test Project"}  # No portfolio_item

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    response = client.get("/linkedin/preview/1")
    assert response.status_code == 404
    assert "portfolio" in response.json()["detail"].lower()


def test_get_linkedin_preview_without_hashtags(monkeypatch, mock_project_data):
    """Test preview generation without hashtags"""

    def mock_load_project_insight_by_id(self, project_id):
        return mock_project_data

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    response = client.get("/linkedin/preview/1?include_hashtags=false")
    assert response.status_code == 200

    data = response.json()
    assert len(data["hashtags"]) == 0
    assert "#" not in data["text"]


def test_get_linkedin_preview_without_emojis(monkeypatch, mock_project_data):
    """Test preview generation without emojis"""

    def mock_load_project_insight_by_id(self, project_id):
        return mock_project_data

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    response = client.get("/linkedin/preview/1?include_emojis=false")
    assert response.status_code == 200

    data = response.json()
    common_emojis = ["🚀", "💻", "✨", "📊"]
    assert not any(emoji in data["text"] for emoji in common_emojis)


def test_get_custom_linkedin_preview_success(monkeypatch, mock_project_data):
    """Test custom preview with POST endpoint"""

    def mock_load_project_insight_by_id(self, project_id):
        return mock_project_data

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    payload = {"include_hashtags": False, "include_emojis": True}
    response = client.post("/linkedin/preview/1/custom", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["hashtags"]) == 0
    assert data["char_count"] > 0


def test_get_custom_linkedin_preview_all_disabled(monkeypatch, mock_project_data):
    """Test custom preview with all options disabled"""

    def mock_load_project_insight_by_id(self, project_id):
        return mock_project_data

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    payload = {"include_hashtags": False, "include_emojis": False}
    response = client.post("/linkedin/preview/1/custom", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["hashtags"]) == 0
    common_emojis = ["🚀", "💻", "✨", "📊"]
    assert not any(emoji in data["text"] for emoji in common_emojis)


def test_linkedin_preview_includes_tech_stack(monkeypatch, mock_project_data):
    """Test that preview includes tech stack information"""

    def mock_load_project_insight_by_id(self, project_id):
        return mock_project_data

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    response = client.get("/linkedin/preview/1")
    assert response.status_code == 200

    data = response.json()
    text = data["text"]
    assert "Python" in text
    assert "JavaScript" in text
    assert "FastAPI" in text
    assert "React" in text


def test_portfolio_error_handling(monkeypatch):
    """Test handling of portfolio generation errors"""

    def mock_load_project_insight_by_id(self, project_id):
        return {
            "project_name": "Test",
            "portfolio_item": {"error": "Failed to generate portfolio"},
        }

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    response = client.get("/linkedin/preview/1")
    assert response.status_code == 404
    assert "failed" in response.json()["detail"].lower()


def test_custom_endpoint_project_not_found(monkeypatch):
    """Test custom endpoint returns 404 for missing project"""

    def mock_load_project_insight_by_id(self, project_id):
        return None

    monkeypatch.setattr(
        ProjectInsightsStore, "load_project_insight_by_id", mock_load_project_insight_by_id
    )

    payload = {"include_hashtags": True, "include_emojis": True}
    response = client.post("/linkedin/preview/999/custom", json=payload)
    assert response.status_code == 404
