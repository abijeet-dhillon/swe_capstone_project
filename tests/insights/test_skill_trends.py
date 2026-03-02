"""Test new skill trends and progression endpoints."""

import pytest
import tempfile
from pathlib import Path

from src.insights.project_filter import ProjectFilterEngine


def test_skill_trends_method():
    """Test get_skill_trends method directly."""
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "test.db"
        
        # Create test database with required schema
        engine = ProjectFilterEngine(db_path=str(db_path))
        
        # Test trends method exists and returns expected structure
        trends = engine.get_skill_trends("python")
        assert isinstance(trends, list)
        
        # Test with non-existent skill
        empty_trends = engine.get_skill_trends("nonexistent")
        assert isinstance(empty_trends, list)


def test_skill_progression_method():
    """Test get_skill_progression method directly."""
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "test.db"
        
        # Create test database with required schema
        engine = ProjectFilterEngine(db_path=str(db_path))
        
        # Test progression method exists and returns expected structure
        progression = engine.get_skill_progression()
        assert isinstance(progression, dict)
        
        # Test empty database
        empty_progression = engine.get_skill_progression()
        assert isinstance(empty_progression, dict)
