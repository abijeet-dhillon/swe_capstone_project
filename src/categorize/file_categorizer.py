"""
file_categorizer.py
-------------------
Responsible for categorizing a given extracted folder that may contain nested subfolders and files,
and producing a structured JSON representation of the directory hierarchy.

Run from root directory with:
    docker compose run --rm backend python -m src.categorize.file_categorizer
"""

from pathlib import Path
import os
import json

code_exts = {".py", ".js", ".java", ".cpp", ".c", ".h", ".cs", ".ts", ".rb", ".go", ".php", ".ipynb"}
doc_exts = {".md", ".txt", ".pdf", ".docx", ".rtf"}
image_exts = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".bmp"}
sketch_exts = {".drawio", ".vsdx", ".sketch", ".fig", ".xd"}
ignore_exts = {".git", "__pycache__", "node_modules"}

def categorize_file(filename: str) -> str:
    """ Return a category label based on the file extension. """
    ext = Path(filename).suffix.lower()
    if ext in code_exts:
        return "code"
    elif ext in doc_exts:
        return "documentation"
    elif ext in image_exts:
        return "images"
    elif ext in sketch_exts:
        return "sketches"
    else:
        return "other"
    
def categorize_folder_structure(folder_path: str) -> dict:
    """
        Walk through a folder hierarchy and produce a structured, categorized representation.
        Args:
            folder_path (str): Path to the folder to parse.
        Returns:
            dict: A nested JSON-style dictionary representing the folder structure and categorized files.
    """
    root_folder = Path(folder_path)
    if not root_folder.exists() or not root_folder.is_dir():
        raise ValueError(f"ERROR: Invalid path: {root_folder}")
    
    structured_representation = {}
    
    for current_path, subdirs, files in os.walk(root_folder, topdown=True):
        subdirs[:] = [d for d in subdirs if d not in ignore_exts]

        relative_path = str(Path(current_path).relative_to(root_folder)) or "."

        categorized = {
            "code": [],
            "documentation": [],
            "images": [],
            "sketches": [],
            "other": []
        }

        for filename in files:
            category = categorize_file(filename)
            categorized[category].append(filename)

        structured_representation[relative_path] = categorized

    return structured_representation