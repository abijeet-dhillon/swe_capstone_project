"""
test_file_categorizer.py
------------------------
Tests for file_categorizer.py using pytest.
Ensures categorized folder structure is correctly returned as JSON-style dict,
and now also verifies language-based categorization (code_by_language).

Run from root directory with:
    docker compose run --rm backend python3 -m pytest tests/categorize/test_file_categorizer.py -v
    or 
    python3 -m pytest tests/categorize/test_file_categorizer.py -v
"""

import pytest
import tempfile
from pathlib import Path
from src.categorize.file_categorizer import (
    categorize_folder_structure,
    categorize_file,
)

@pytest.fixture
def temp_project_dir():
    """Create a temporary folder with a mock project hierarchy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Folder structure
        (base / "project1").mkdir()
        (base / "project1" / "docs").mkdir()
        (base / "project1" / "images").mkdir()
        (base / "emptydir").mkdir()
        # Code files (multiple languages)
        (base / "project1" / "main.py").write_text("print('hello')")
        (base / "project1" / "helper.cpp").write_text("int main(){}")
        (base / "project1" / "App.java").write_text("class App {}")
        (base / "project1" / "script.sh").write_text("echo hi")
        # Non-code files
        (base / "project1" / "README.md").write_text("# Readme")
        (base / "project1" / "docs" / "design.pdf").write_text("pdf data")
        (base / "project1" / "images" / "diagram.png").write_bytes(b"imagebytes")
        (base / "notes.txt").write_text("root note")

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
    # Verify expected directories
    assert "." in result
    assert "project1" in result
    assert "project1/docs" in result
    assert "project1/images" in result
    assert "emptydir" in result
    # Check required keys exist in every folder
    for data in result.values():
        for key in ["code", "documentation", "images", "sketches", "other", "code_by_language"]:
            assert key in data
    # Check correct categorization of files
    proj1 = result["project1"]
    assert "main.py" in proj1["code"]
    assert "README.md" in proj1["documentation"]
    assert "helper.cpp" in proj1["code"]
    assert "App.java" in proj1["code"]
    assert "script.sh" in proj1["code"]
    assert "design.pdf" in result["project1/docs"]["documentation"]
    assert "diagram.png" in result["project1/images"]["images"]
    assert "notes.txt" in result["."]["documentation"]
    # --- Verify code_by_language breakdown ---
    code_langs = proj1["code_by_language"]
    assert "python" in code_langs
    assert "cpp" in code_langs
    assert "java" in code_langs
    assert "shell" in code_langs
    assert "main.py" in code_langs["python"]
    assert "helper.cpp" in code_langs["cpp"]
    assert "App.java" in code_langs["java"]
    assert "script.sh" in code_langs["shell"]

def test_invalid_path_raises_valueerror():
    """Test Scenario: Invalid folder path should raise ValueError."""
    with pytest.raises(ValueError):
        categorize_folder_structure("/non/existent/path")

def test_empty_directory_returns_empty_categories(temp_project_dir):
    """Test Scenario: Empty folder should still produce category keys with empty lists."""
    result = categorize_folder_structure(temp_project_dir)
    empty_dir = result["emptydir"]
    for key in ["code", "documentation", "images", "sketches", "other", "code_by_language"]:
        assert key in empty_dir
        # code_by_language should be dict, others are lists
        if key == "code_by_language":
            assert isinstance(empty_dir[key], dict)
            assert empty_dir[key] == {}
        else:
            assert empty_dir[key] == []