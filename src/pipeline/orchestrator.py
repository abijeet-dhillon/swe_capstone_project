"""
Pipeline Orchestrator
Connects ZIP parser and file categorizer components
"""

import json
from pathlib import Path
from typing import Dict, Any

from src.ingest.zip_parser import categorize_parse_zip


class ArtifactPipeline:
    """
    Orchestrator that connects the ZIP parser and file categorizer.
    
    Usage:
        pipeline = ArtifactPipeline()
        result = pipeline.start('/path/to/project.zip')
        print(result['categorized_contents'])
    """
    
    def __init__(self):
        """Initialize the pipeline orchestrator"""
        pass
    
    def start(self, zip_path: str) -> Dict[str, Any]:
        """
        Main entry point - parse ZIP and categorize files
        
        Args:
            zip_path: Path to the ZIP file to analyze
            
        Returns:
            Dictionary containing:
                - zip_metadata: Info about the ZIP file (name, file count, sizes)
                - file_info: List of file metadata (paths, sizes, hashes)
                - categorized_contents: Dictionary mapping file types to file paths
                    {
                        "code": [list of code file paths],
                        "code_by_language": {language: [file paths]},
                        "documentation": [list of doc file paths],
                        "images": [list of image file paths],
                        "sketches": [list of sketch file paths],
                        "other": [list of other file paths]
                    }
        """
        # Validate input
        zip_path = Path(zip_path)
        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        
        if not zip_path.suffix.lower() == '.zip':
            raise ValueError(f"File must be a ZIP archive, got: {zip_path.suffix}")
        
        print(f"\n{'='*70}")
        print(f"🚀 Starting Artifact Pipeline")
        print(f"{'='*70}")
        print(f"📦 ZIP File: {zip_path.name}")
        
        # Step 1 & 2: Parse ZIP and categorize files
        # (Both steps are handled by categorize_parse_zip)
        print(f"\n[1/2] Parsing ZIP file...")
        print(f"[2/2] Categorizing extracted files...")
        
        result = categorize_parse_zip(str(zip_path))
        
        if not result:
            raise RuntimeError("Failed to parse and categorize ZIP file")
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    def _print_summary(self, result: Dict[str, Any]) -> None:
        """Print a summary of the analysis results"""
        print(f"\n{'='*70}")
        print(f"✅ Pipeline Complete!")
        print(f"{'='*70}")
        
        # ZIP metadata summary
        zip_meta = result.get('zip_metadata', {})
        print(f"\n📊 ZIP Summary:")
        print(f"   • Total files: {zip_meta.get('file_count', 0)}")
        print(f"   • Uncompressed size: {self._format_bytes(zip_meta.get('total_uncompressed_bytes', 0))}")
        print(f"   • Compressed size: {self._format_bytes(zip_meta.get('total_compressed_bytes', 0))}")
        
        # Categorization summary
        categorized = result.get('categorized_contents', {})
        print(f"\n📁 Categorization Summary:")
        print(f"   • Code files: {len(categorized.get('code', []))}")
        
        # Show languages breakdown
        code_by_lang = categorized.get('code_by_language', {})
        if code_by_lang:
            print(f"     Languages detected:")
            for lang, files in sorted(code_by_lang.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"       - {lang}: {len(files)} files")
        
        print(f"   • Documentation files: {len(categorized.get('documentation', []))}")
        print(f"   • Image files: {len(categorized.get('images', []))}")
        print(f"   • Sketch files: {len(categorized.get('sketches', []))}")
        print(f"   • Other files: {len(categorized.get('other', []))}")
        
        print(f"\n{'='*70}\n")
    
    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes into human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"


def main():
    """
    Example usage / CLI entry point
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.pipeline.orchestrator <path_to_zip_file>")
        print("Example: python -m src.pipeline.orchestrator ./test_data/project.zip")
        sys.exit(1)
    
    zip_path = sys.argv[1]
    
    try:
        # Create pipeline and run
        pipeline = ArtifactPipeline()
        result = pipeline.start(zip_path)
        
        # Print the categorized contents dictionary
        print("\n📋 Categorized Contents (Dictionary Output):")
        print("="*70)
        print(json.dumps(result['categorized_contents'], indent=2))
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
