# Pipeline Orchestrator

The pipeline orchestrator connects the ZIP parser and file categorizer components to provide a unified interface for analyzing project artifacts.

## Overview

The orchestrator performs two main steps:
1. **Parse ZIP**: Extracts and validates the ZIP file, computing metadata and hashes
2. **Categorize Files**: Classifies extracted files by type (code, documentation, images, etc.)

## Usage

### From Command Line

```bash
# Using the module directly (from root dir)
python3 -m src.pipeline.orchestrator tests/categorize/demo_projects.zip
```

## Output Format

The `start()` method returns a dictionary with three main sections:

```json
{
  "zip_metadata": {
    "root_name": "project.zip",
    "file_count": 127,
    "total_uncompressed_bytes": 5242880,
    "total_compressed_bytes": 2621440
  },
  "file_info": [
    {
      "abs_path": "/tmp/unzipped_xyz/src/main.py",
      "rel_path": "src/main.py",
      "size": 1024,
      "compressed_size": 512,
      "is_compressed": true,
      "sha256": "abc123...",
      "depth": 1,
      "ext": "py",
      "is_text_guess": true
    }
  ],
  "categorized_contents": {
    "code": ["/tmp/unzipped_xyz/src/main.py", ...],
    "code_by_language": {
      "python": ["/tmp/unzipped_xyz/src/main.py", ...],
      "javascript": ["/tmp/unzipped_xyz/app.js", ...]
    },
    "documentation": ["/tmp/unzipped_xyz/README.md", ...],
    "images": ["/tmp/unzipped_xyz/logo.png", ...],
    "sketches": ["/tmp/unzipped_xyz/design.drawio", ...],
    "other": ["/tmp/unzipped_xyz/data.csv", ...]
  }
}
```

## Categorized Contents Structure

The `categorized_contents` dictionary contains:

- **`code`**: List of all code file paths
- **`code_by_language`**: Dictionary mapping language names to file paths
  - Supported languages: python, javascript, typescript, java, cpp, c, go, rust, ruby, php, swift, kotlin, scala, etc.
- **`documentation`**: List of documentation file paths (.md, .txt, .pdf, .docx, .rtf)
- **`images`**: List of image file paths (.png, .jpg, .jpeg, .gif, .svg, .bmp)
- **`sketches`**: List of design file paths (.drawio, .vsdx, .sketch, .fig, .xd)
- **`other`**: List of uncategorized file paths

## Example Output

```
======================================================================
🚀 Starting Artifact Pipeline
======================================================================
📦 ZIP File: my_project.zip

[1/2] Parsing ZIP file...
[INFO] Parsed ZIP 'my_project.zip' with 45 files
[INFO] Extracting ZIP to temporary folder: /tmp/unzipped_abc123
[2/2] Categorizing extracted files...

======================================================================
✅ Pipeline Complete!
======================================================================

📊 ZIP Summary:
   • Total files: 45
   • Uncompressed size: 2.50 MB
   • Compressed size: 1.25 MB

📁 Categorization Summary:
   • Code files: 30
     Languages detected:
       - python: 20 files
       - javascript: 10 files
   • Documentation files: 8
   • Image files: 5
   • Sketch files: 2
   • Other files: 0

======================================================================
```

## Next Steps

This orchestrator will be extended to:
1. Call the appropriate analyzers for each file type (code analyzer, text analyzer, etc.)
2. Aggregate analysis results
3. Generate the final report

## Testing

```bash
# Test with a sample ZIP file (from root dir)
python3 -m src.pipeline.orchestrator tests/categorize/demo_projects.zip

# Output will be saved to orchestrator_output.json
```
