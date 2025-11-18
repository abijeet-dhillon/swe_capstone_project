"""
Pipeline Orchestrator
Connects ZIP parser, file categorizer, and local analyzer components
"""

import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

from src.ingest.zip_parser import parse_zip
from src.categorize.file_categorizer import categorize_folder_structure
from src.analyze.text_analyzer import TextAnalyzer
from src.analyze.code_analyzer import CodeAnalyzer
from src.analyze.video_analyzer import VideoAnalyzer
from src.image_processor import ImageProcessor


class ArtifactPipeline:
    """
    Orchestrator that connects the ZIP parser, file categorizer, and local analyzers.
    
    Usage:
        pipeline = ArtifactPipeline()
        result = pipeline.start('/path/to/project.zip')
        print(result['analysis_results'])
    """
    
    # Video file extensions to detect in "other" category
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv'}
    
    def __init__(self):
        """Initialize the pipeline orchestrator and all analyzers"""
        self.text_analyzer = TextAnalyzer()
        self.code_analyzer = CodeAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        self.image_processor = ImageProcessor()
        self.temp_dir = None
    
    def start(self, zip_path: str) -> Dict[str, Any]:
        """
        Main entry point - parse ZIP, categorize files, and analyze with local analyzers
        
        Args:
            zip_path: Path to the ZIP file to analyze
            
        Returns:
            Dictionary containing:
                - zip_metadata: Info about the ZIP file (name, file count, sizes)
                - file_info: List of file metadata (paths, sizes, hashes)
                - categorized_contents: Dictionary mapping file types to file paths
                - analysis_results: Dictionary containing analysis results from each analyzer
                    {
                        "documentation": {...results from TextAnalyzer...},
                        "images": [...results from ImageProcessor...],
                        "code": [...results from CodeAnalyzer...],
                        "videos": [...results from VideoAnalyzer...]
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
        
        try:
            # Step 1: Parse ZIP metadata
            print(f"\n[1/5] Parsing ZIP file metadata...")
            zip_index = parse_zip(str(zip_path))
            print(f"✓ Parsed {zip_index.file_count} files")
            
            # Step 2: Extract to temporary directory
            print(f"\n[2/5] Extracting ZIP contents...")
            self.temp_dir = Path(tempfile.mkdtemp(prefix="unzipped_"))
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(self.temp_dir)
            print(f"✓ Extracted to: {self.temp_dir}")
            
            # Step 3: Categorize extracted files
            print(f"\n[3/5] Categorizing files by type...")
            categorized_contents = categorize_folder_structure(str(self.temp_dir))
            print(f"✓ Categorized into {len([k for k in categorized_contents.keys() if k != 'code_by_language'])} categories")
            
            # Build file info list
            file_info = []
            for entry in zip_index.files:
                if "__MACOSX" in entry.rel_path or Path(entry.rel_path).name.startswith("._"):
                    continue
                extracted_path = self.temp_dir / entry.rel_path
                if not extracted_path.exists():
                    continue
                file_info.append({
                    "abs_path": str(extracted_path.resolve()),
                    "rel_path": entry.rel_path,
                    "size": entry.size,
                    "compressed_size": entry.compressed_size,
                    "is_compressed": entry.is_compressed,
                    "sha256": entry.sha256,
                    "depth": entry.depth,
                    "ext": entry.ext,
                    "is_text_guess": entry.is_text_guess,
                })
            
            # Step 4: Analyze files with appropriate analyzers
            print(f"\n[4/5] Analyzing files with local analyzers...")
            analysis_results = self._analyze_categorized_files(categorized_contents)
            
            # Step 5: Build final result
            print(f"\n[5/5] Compiling results...")
            result = {
                "zip_metadata": {
                    "root_name": zip_index.root_name,
                    "file_count": zip_index.file_count,
                    "total_uncompressed_bytes": zip_index.total_uncompressed_bytes,
                    "total_compressed_bytes": zip_index.total_compressed_bytes,
                },
                "file_info": file_info,
                "categorized_contents": categorized_contents,
                "analysis_results": analysis_results
            }
            
            # Print summary
            self._print_summary(result)
            
            return result
            
        finally:
            # Always clean up temp directory
            if self.temp_dir and self.temp_dir.exists():
                print(f"\n🧹 Cleaning up temporary directory...")
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _analyze_categorized_files(self, categorized_contents: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze files by category using appropriate analyzers
        
        Args:
            categorized_contents: Dictionary from file categorizer
            
        Returns:
            Dictionary with analysis results for each category
        """
        results = {}
        
        # Analyze documentation files (PDF, DOCX, TXT, MD)
        doc_files = categorized_contents.get('documentation', [])
        if doc_files:
            print(f"  📄 Analyzing {len(doc_files)} documentation file(s)...")
            try:
                results['documentation'] = self.text_analyzer.analyze_batch(doc_files)
                print(f"     ✓ Documentation analysis complete")
            except Exception as e:
                print(f"     ✗ Error analyzing documentation: {e}")
                results['documentation'] = {"error": str(e)}
        else:
            print(f"  📄 No documentation files to analyze")
            results['documentation'] = None
        
        # Analyze image files (PNG, JPG, JPEG, etc.)
        image_files = categorized_contents.get('images', [])
        if image_files:
            print(f"  🖼️  Analyzing {len(image_files)} image file(s)...")
            try:
                results['images'] = self.image_processor.batch_analyze(image_files)
                print(f"     ✓ Image analysis complete")
            except Exception as e:
                print(f"     ✗ Error analyzing images: {e}")
                results['images'] = {"error": str(e)}
        else:
            print(f"  🖼️  No image files to analyze")
            results['images'] = None
        
        # Analyze code files
        code_files = categorized_contents.get('code', [])
        if code_files:
            print(f"  💻 Analyzing {len(code_files)} code file(s)...")
            try:
                # CodeAnalyzer needs to be called per file
                code_results = []
                for code_file in code_files:
                    try:
                        analysis = self.code_analyzer.analyze_file(code_file)
                        code_results.append(analysis.to_dict())
                    except Exception as e:
                        print(f"     ⚠️  Warning: Could not analyze {Path(code_file).name}: {e}")
                        continue
                
                # Calculate aggregate metrics
                from src.analyze.code_analyzer import AnalysisResult
                analysis_objs = []
                for r in code_results:
                    analysis_objs.append(AnalysisResult(**r))
                
                metrics = self.code_analyzer.calculate_contribution_metrics(analysis_objs)
                
                results['code'] = {
                    'files': code_results,
                    'metrics': metrics.to_dict()
                }
                print(f"     ✓ Code analysis complete ({len(code_results)} files)")
            except Exception as e:
                print(f"     ✗ Error analyzing code: {e}")
                results['code'] = {"error": str(e)}
        else:
            print(f"  💻 No code files to analyze")
            results['code'] = None
        
        # Analyze video files (check "other" category for video extensions)
        other_files = categorized_contents.get('other', [])
        video_files = [f for f in other_files if Path(f).suffix.lower() in self.VIDEO_EXTENSIONS]
        
        if video_files:
            print(f"  🎥 Analyzing {len(video_files)} video file(s)...")
            try:
                # VideoAnalyzer needs to be called per file
                video_results = []
                for video_file in video_files:
                    try:
                        analysis = self.video_analyzer.analyze_file(video_file, transcribe=False)
                        if analysis:
                            video_results.append(analysis.to_dict())
                    except Exception as e:
                        print(f"     ⚠️  Warning: Could not analyze {Path(video_file).name}: {e}")
                        continue
                
                # Calculate collection metrics
                from src.analyze.video_analyzer import VideoAnalysisResult
                video_objs = []
                for r in video_results:
                    video_objs.append(VideoAnalysisResult(**r))
                
                metrics = self.video_analyzer.calculate_collection_metrics(video_objs)
                
                results['videos'] = {
                    'files': video_results,
                    'metrics': metrics.to_dict()
                }
                print(f"     ✓ Video analysis complete ({len(video_results)} files)")
            except Exception as e:
                print(f"     ✗ Error analyzing videos: {e}")
                results['videos'] = {"error": str(e)}
        else:
            print(f"  🎥 No video files to analyze")
            results['videos'] = None
        
        return results
    
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
        
        # Analysis summary
        analysis = result.get('analysis_results', {})
        print(f"\n🔍 Analysis Summary:")
        
        # Documentation analysis
        doc_analysis = analysis.get('documentation')
        if doc_analysis and doc_analysis is not None and 'error' not in doc_analysis:
            totals = doc_analysis.get('totals', {})
            print(f"   • Documentation:")
            print(f"     - {totals.get('total_files', 0)} files analyzed")
            print(f"     - {totals.get('total_words', 0):,} total words")
            print(f"     - {totals.get('total_reading_time_minutes', 0):.1f} minutes reading time")
        
        # Image analysis
        img_analysis = analysis.get('images')
        if img_analysis and img_analysis is not None and 'error' not in img_analysis:
            print(f"   • Images:")
            print(f"     - {len(img_analysis)} files analyzed")
            if img_analysis:
                total_size = sum(img.get('file_stats', {}).get('size_mb', 0) for img in img_analysis)
                print(f"     - {total_size:.2f} MB total size")
        
        # Code analysis
        code_analysis = analysis.get('code')
        if code_analysis and code_analysis is not None and 'error' not in code_analysis:
            metrics = code_analysis.get('metrics', {})
            print(f"   • Code:")
            print(f"     - {metrics.get('total_files', 0)} files analyzed")
            print(f"     - {metrics.get('total_lines', 0):,} total lines of code")
            langs = metrics.get('languages', [])
            if langs:
                print(f"     - Languages: {', '.join(langs)}")
            frameworks = metrics.get('frameworks', [])
            if frameworks:
                print(f"     - Frameworks: {', '.join(frameworks[:5])}")
        
        # Video analysis
        video_analysis = analysis.get('videos')
        if video_analysis and video_analysis is not None and 'error' not in video_analysis:
            metrics = video_analysis.get('metrics', {})
            print(f"   • Videos:")
            print(f"     - {metrics.get('total_videos', 0)} files analyzed")
            print(f"     - {metrics.get('total_duration', 0):.1f} seconds total duration")
        
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
        print("Example: python -m src.pipeline.orchestrator ./tests/categorize/demo_projects.zip")
        sys.exit(1)
    
    zip_path = sys.argv[1]
    
    try:
        # Create pipeline and run
        pipeline = ArtifactPipeline()
        result = pipeline.start(zip_path)
        
        # Print detailed analysis results
        print("\n" + "="*70)
        print("📋 DETAILED ANALYSIS RESULTS")
        print("="*70)
        
        analysis = result.get('analysis_results', {})
        
        # Documentation Analysis Details
        if analysis.get('documentation'):
            print("\n" + "-"*70)
            print("📄 DOCUMENTATION ANALYSIS")
            print("-"*70)
            doc_data = analysis['documentation']
            if 'error' in doc_data:
                print(f"Error: {doc_data['error']}")
            else:
                print(json.dumps(doc_data, indent=2))
        
        # Image Analysis Details
        if analysis.get('images'):
            print("\n" + "-"*70)
            print("🖼️  IMAGE ANALYSIS")
            print("-"*70)
            img_data = analysis['images']
            if 'error' in img_data:
                print(f"Error: {img_data['error']}")
            else:
                # Print summary for each image (full output can be very large)
                for i, img in enumerate(img_data, 1):
                    print(f"\n[Image {i}] {img.get('file_name', 'unknown')}")
                    print(f"  Resolution: {img.get('resolution', {}).get('width', 0)}x{img.get('resolution', {}).get('height', 0)}")
                    print(f"  Size: {img.get('file_stats', {}).get('size_mb', 0):.2f} MB")
                    print(f"  Format: {img.get('format', {}).get('format', 'unknown')}")
                    content = img.get('content_classification', {})
                    print(f"  Type: {content.get('primary_type', 'unknown')}")
        
        # Code Analysis Details
        if analysis.get('code'):
            print("\n" + "-"*70)
            print("💻 CODE ANALYSIS")
            print("-"*70)
            code_data = analysis['code']
            if 'error' in code_data:
                print(f"Error: {code_data['error']}")
            else:
                print(json.dumps(code_data, indent=2))
        
        # Video Analysis Details
        if analysis.get('videos'):
            print("\n" + "-"*70)
            print("🎥 VIDEO ANALYSIS")
            print("-"*70)
            video_data = analysis['videos']
            if 'error' in video_data:
                print(f"Error: {video_data['error']}")
            else:
                print(json.dumps(video_data, indent=2))
        
        print("\n" + "="*70)
        print("✅ Analysis Complete - All results printed above")
        print("="*70 + "\n")
        
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
