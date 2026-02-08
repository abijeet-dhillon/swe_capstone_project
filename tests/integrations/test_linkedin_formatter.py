"""Tests for LinkedIn formatter"""
from __future__ import annotations

import pytest
from src.integrations.linkedin_formatter import LinkedInFormatter


@pytest.fixture
def sample_portfolio():
    """Sample portfolio item for testing"""
    return {
        "project_name": "TaskFlow API",
        "tagline": "A modern task management REST API",
        "description": "Built a scalable REST API for task management with user authentication, real-time updates, and comprehensive testing.",
        "languages": ["Python", "JavaScript", "SQL"],
        "frameworks": ["FastAPI", "React", "PostgreSQL"],
        "skills": ["REST API Design", "Database Architecture", "Testing"],
        "is_collaborative": False,
        "total_commits": 156,
        "total_lines": 5420,
        "total_files": 45,
    }


def test_format_portfolio_post_basic(sample_portfolio):
    """Test basic portfolio formatting returns all required fields"""
    formatter = LinkedInFormatter()
    result = formatter.format_portfolio_post(sample_portfolio)
    assert "text" in result and "char_count" in result and "hashtags" in result
    assert result["exceeds_limit"] is False
    assert result["char_count"] <= 3000 and result["char_count"] > 0


def test_format_includes_content(sample_portfolio):
    """Test formatted text includes key content"""
    formatter = LinkedInFormatter()
    result = formatter.format_portfolio_post(sample_portfolio)
    assert sample_portfolio["project_name"] in result["text"]
    assert "Python" in result["text"] and "FastAPI" in result["text"]


def test_format_with_and_without_hashtags(sample_portfolio):
    """Test hashtag inclusion/exclusion"""
    formatter = LinkedInFormatter()
    with_tags = formatter.format_portfolio_post(sample_portfolio, include_hashtags=True)
    without_tags = formatter.format_portfolio_post(sample_portfolio, include_hashtags=False)
    assert len(with_tags["hashtags"]) > 0 and "#" in with_tags["text"]
    assert len(without_tags["hashtags"]) == 0 and "#" not in without_tags["text"]


def test_format_with_and_without_emojis(sample_portfolio):
    """Test emoji inclusion/exclusion"""
    formatter = LinkedInFormatter()
    with_emoji = formatter.format_portfolio_post(sample_portfolio, include_emojis=True)
    without_emoji = formatter.format_portfolio_post(sample_portfolio, include_emojis=False)
    assert any(e in with_emoji["text"] for e in ["🚀", "💻", "✨", "📊"])
    assert not any(e in without_emoji["text"] for e in ["🚀", "💻", "✨", "📊"])


def test_truncate_long_content():
    """Test long content is truncated to fit limit"""
    long_portfolio = {
        "project_name": "Test",
        "tagline": "Test",
        "description": "A" * 2000,
        "languages": ["Python"] * 50,
        "frameworks": ["Framework"] * 50,
        "skills": ["Skill"] * 50,
    }
    formatter = LinkedInFormatter()
    result = formatter.format_portfolio_post(long_portfolio)
    assert result["char_count"] <= 3000 and not result["exceeds_limit"]


def test_minimal_portfolio():
    """Test formatting with minimal data"""
    minimal = {
        "project_name": "Simple Project",
        "tagline": "Test",
        "description": "Basic",
        "languages": [],
        "frameworks": [],
        "skills": [],
    }
    formatter = LinkedInFormatter()
    result = formatter.format_portfolio_post(minimal)
    assert result["text"] and minimal["project_name"] in result["text"]


def test_none_values_handling():
    """Test handling of None values"""
    portfolio = {
        "project_name": "Test",
        "tagline": None,
        "description": "Valid",
        "languages": None,
        "frameworks": None,
        "skills": None,
    }
    formatter = LinkedInFormatter()
    result = formatter.format_portfolio_post(portfolio)
    assert result["text"] and "Test" in result["text"]


def test_collaborative_vs_individual_cta(sample_portfolio):
    """Test different CTAs for collaborative vs individual projects"""
    formatter = LinkedInFormatter()
    individual = formatter.format_portfolio_post(sample_portfolio)
    sample_portfolio["is_collaborative"] = True
    collaborative = formatter.format_portfolio_post(sample_portfolio)
    assert "team" in collaborative["text"].lower() or "collaborat" in collaborative["text"].lower()
    assert individual["text"] != collaborative["text"]
