"""Tests for git_identifier functionality in orchestrator"""
import pytest
from src.pipeline.orchestrator import ArtifactPipeline


def test_extract_user_contribution_by_email():
    pipeline = ArtifactPipeline(enable_insights=False)
    contributors = [
        {"author": {"name": "Alice", "email": "alice@example.com"}, "commits": 10},
        {"author": {"name": "Bob", "email": "bob@example.com"}, "commits": 5},
    ]
    
    result = pipeline._extract_user_contribution(contributors, "alice@example.com")
    assert result is not None
    assert result["commits"] == 10


def test_extract_user_contribution_by_partial_email():
    pipeline = ArtifactPipeline(enable_insights=False)
    contributors = [
        {"author": {"name": "Alice", "email": "alice@example.com"}, "commits": 10},
    ]
    
    result = pipeline._extract_user_contribution(contributors, "alice")
    assert result is not None
    assert result["commits"] == 10


def test_extract_user_contribution_by_name():
    pipeline = ArtifactPipeline(enable_insights=False)
    contributors = [
        {"author": {"name": "Alice Smith", "email": "a@example.com"}, "commits": 10},
    ]
    
    result = pipeline._extract_user_contribution(contributors, "alice")
    assert result is not None
    assert result["commits"] == 10


def test_extract_user_contribution_not_found():
    pipeline = ArtifactPipeline(enable_insights=False)
    contributors = [
        {"author": {"name": "Alice", "email": "alice@example.com"}, "commits": 10},
    ]
    
    result = pipeline._extract_user_contribution(contributors, "charlie")
    assert result is None
