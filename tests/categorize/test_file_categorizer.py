"""
test_file_categorizer.py
------------------------
Tests for file_categorizer.py using pytest.
Ensures categorized folder structure is correctly returned as JSON-style dict.
"""

import pytest
import tempfile
from pathlib import Path

from src.categorize.file_categorizer import categorize_folder_structure, categorize_file


@pytest.fixture
def temp_project_dir():
    """Create a temporary folder with a mock project hierarchy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        (base / "project1").mkdir()
        (base / "project1" / "docs").mkdir()
        (base / "project1" / "images").mkdir()
        (base / "emptydir").mkdir()

        (base / "project1" / "main.py").write_text("print('hello')")
        (base / "project1" / "README.md").write_text("# Readme")
        (base / "project1" / "docs" / "design.pdf").write_text("pdf data")
        (base / "project1" / "images" / "diagram.png").write_bytes(b"imagebytes")
        (base / "notes.txt").write_text("root note")
        (base / "script.sh").write_text("echo hi")

        yield base


def test_categorize_file_by_extension():
    """Test Scenario: Verify correct category is assigned based on file extension."""
    assert categorize_file("script.py") == "code"
    assert categorize_file("notes.txt") == "documentation"
    assert categorize_file("diagram.png") == "images"
    assert categorize_file("design.drawio") == "sketches"
    assert categorize_file("random.bin") == "other"


def test_structure_keys_and_categories(temp_project_dir):
    """Test Scenario: Ensure output contains correct folder keys and categories."""
    result = categorize_folder_structure(temp_project_dir)

    assert "." in result
    assert "project1" in result
    assert "project1/docs" in result
    assert "project1/images" in result
    assert "emptydir" in result

    for data in result.values():
        for key in ["code", "documentation", "images", "sketches", "other"]:
            assert key in data

    assert "main.py" in result["project1"]["code"]
    assert "README.md" in result["project1"]["documentation"]
    assert "design.pdf" in result["project1/docs"]["documentation"]
    assert "diagram.png" in result["project1/images"]["images"]
    assert "notes.txt" in result["."]["documentation"]
    assert "script.sh" in result["."]["other"]


def test_invalid_path_raises_valueerror():
    """Test Scenario: Invalid folder path should raise ValueError."""
    with pytest.raises(ValueError):
        categorize_folder_structure("/non/existent/path")


def test_empty_directory_returns_empty_categories(temp_project_dir):
    """Test Scenario: Empty folder should still produce category keys with empty lists."""
    result = categorize_folder_structure(temp_project_dir)
    empty_dir = result["emptydir"]
    for key in ["code", "documentation", "images", "sketches", "other"]:
        assert key in empty_dir
        assert empty_dir[key] == []
