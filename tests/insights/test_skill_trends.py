"""Test new skill trends and progression endpoints."""

import pytest
import tempfile
import sqlite3
from pathlib import Path

from src.insights.project_filter import ProjectFilterEngine


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database with required schema."""
    db_path = tmp_path / "test_filter.db"
    
    with sqlite3.connect(str(db_path)) as conn:
        # Create required tables (same as test_project_filter.py)
        conn.executescript("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                slug TEXT,
                root_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            CREATE TABLE project_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                total_files INTEGER DEFAULT 0,
                total_lines INTEGER DEFAULT 0,
                total_commits INTEGER DEFAULT 0,
                total_contributors INTEGER DEFAULT 0,
                is_git_repo INTEGER DEFAULT 0,
                tags_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tag_type TEXT NOT NULL
            );
            
            CREATE TABLE skill_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_info_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                FOREIGN KEY (file_info_id) REFERENCES file_info(id),
                FOREIGN KEY (tag_id) REFERENCES tags(id)
            );
            
            CREATE TABLE file_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_info_id INTEGER NOT NULL,
                FOREIGN KEY (project_info_id) REFERENCES project_info(id)
            );
        """)
        conn.commit()
    
    return str(db_path)


def test_skill_trends_method(temp_db):
    """Test get_skill_trends method directly."""
    engine = ProjectFilterEngine(db_path=temp_db)
    
    # Test trends method exists and returns expected structure
    trends = engine.get_skill_trends("python")
    assert isinstance(trends, list)
    
    # Test with non-existent skill
    empty_trends = engine.get_skill_trends("nonexistent")
    assert isinstance(empty_trends, list)


def test_skill_progression_method(temp_db):
    """Test get_skill_progression method directly."""
    engine = ProjectFilterEngine(db_path=temp_db)
    
    # Test progression method exists and returns expected structure
    progression = engine.get_skill_progression()
    assert isinstance(progression, dict)
    
    # Test empty database
    empty_progression = engine.get_skill_progression()
    assert isinstance(empty_progression, dict)
