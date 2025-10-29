"""
tests/test_chronological_skills.py
---
Unit tests for the ChronologicalSkillList class in src/analyze/chronological_skills.py.

These tests verify:
    - correct detection of skills from CodeAnalyzer
    - chronological ordering based on file modification times
    - identification of new skills over time
---
    Run from root directory with:
        docker compose run --rm backend pytest tests/analyze/test_chronological_skills.py --cov=src.analyze.chronological_skills --cov-report=term-missing -v
"""

import os
import time
from pathlib import Path
from datetime import datetime
from src.analyze.chronological_skills import ChronologicalSkillList


def create_temp_code_file(tmp_path: Path, name: str, content: str, delay: float = 0.1) -> Path:
    """
    Helper to create a temporary file and adjust its modification timestamp.
    """
    file_path = tmp_path / name
    file_path.write_text(content, encoding="utf-8")
    # wait to ensure unique timestamps
    time.sleep(delay)
    return file_path


def test_build_skill_timeline(tmp_path):
    """
    Ensure skill timeline events are correctly ordered by modification time.
    """
    # create mock code files with simple content
    f1 = create_temp_code_file(tmp_path, "app.py", "import flask\nprint('Hello')")
    f2 = create_temp_code_file(tmp_path, "test_app.py", "import pytest\ndef test_something(): pass")

    builder = ChronologicalSkillList()
    events = builder.build_skill_timeline(tmp_path)

    # confirm events are sorted chronologically
    timestamps = [e["timestamp"] for e in events]
    assert timestamps == sorted(timestamps), "Events should be sorted by modification time"

    # confirm expected languages
    langs = [e["language"] for e in events]
    assert "python" in langs


def test_summarize_evolution_identifies_new_skills(tmp_path):
    """
    Ensure new skills are correctly detected in chronological order.
    """
    # Create mock files with incremental skills
    f1 = create_temp_code_file(tmp_path, "main.py", "import flask")
    f2 = create_temp_code_file(tmp_path, "utils_async.py", "import asyncio\nasync def f(): pass")

    builder = ChronologicalSkillList()
    events = builder.build_skill_timeline(tmp_path)
    timeline = builder.summarize_evolution(events)

    # Validate chronological summary
    all_new_skills = [s for entry in timeline for s in entry["new_skills"]]
    assert "python" in all_new_skills
    assert any("flask" in s for s in all_new_skills)
    assert any("asynchronous-programming" in s for s in all_new_skills)

    # Check ordering
    dates = [datetime.strptime(entry["date"], "%Y-%m-%d %H:%M:%S") for entry in timeline]
    assert dates == sorted(dates), "Timeline should be chronological"


def test_no_duplicate_skills_in_timeline(tmp_path):
    """
    Verify that once a skill appears, it doesn't reappear in later events.
    """
    f1 = create_temp_code_file(tmp_path, "a.py", "import flask")
    f2 = create_temp_code_file(tmp_path, "b.py", "import flask\nimport pytest")

    builder = ChronologicalSkillList()
    events = builder.build_skill_timeline(tmp_path)
    timeline = builder.summarize_evolution(events)

    # Flatten new skills and ensure no duplicates
    seen = set()
    for entry in timeline:
        for skill in entry["new_skills"]:
            assert skill not in seen, f"Skill '{skill}' appeared more than once"
            seen.add(skill)
