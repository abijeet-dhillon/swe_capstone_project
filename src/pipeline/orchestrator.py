"""
Pipeline Orchestrator
Connects ZIP parser, file categorizer, and local analyzer components
"""

import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.ingest.zip_parser import parse_zip
from src.categorize.file_categorizer import categorize_folder_structure
from src.analyze.text_analyzer import TextAnalyzer
from src.analyze.code_analyzer import CodeAnalyzer
from src.analyze.video_analyzer import VideoAnalyzer
from src.image_processor import ImageProcessor
from src.git.individual_contrib_analyzer import summarize_author_contrib
from src.insights import ProjectInsightsStore


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
    
    def __init__(
        self,
        insights_store: Optional[ProjectInsightsStore] = None,
        enable_insights: bool = True,
    ):
        """
        Initialize the pipeline orchestrator and all analyzers.

        Args:
            insights_store: Optional ProjectInsightsStore used to persist pipeline output.
            enable_insights: When True, automatically initialize the default store if one
                isn't provided (requires INSIGHTS_ENCRYPTION_KEY).
        """
        self.text_analyzer = TextAnalyzer()
        self.code_analyzer = CodeAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        self.image_processor = ImageProcessor()
        self.temp_dir = None
        self.insights_store = insights_store

        if self.insights_store is None and enable_insights:
            try:
                self.insights_store = ProjectInsightsStore()
            except Exception as exc:  # pragma: no cover - warning path
                print(f"⚠️  Insights storage disabled: {exc}")
                self.insights_store = None
    
    def start(self, zip_path: str) -> Dict[str, Any]:
        """
        Main entry point - parse ZIP, identify projects, analyze each project
        
        Args:
            zip_path: Path to the ZIP file to analyze
            
        Returns:
            Dictionary containing:
                - zip_metadata: Info about the ZIP file
                - projects: Dictionary where each key is a project name (top-level directory)
                    Each project contains:
                        - is_git_repo: bool
                        - git_analysis: {...} (if Git repo)
                        - categorized_contents: file categorization
                        - analysis_results: results from analyzers by file type
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
            print(f"\n[1/6] Parsing ZIP file metadata...")
            zip_index = parse_zip(str(zip_path))
            print(f"✓ Parsed {zip_index.file_count} files")
            
            # Step 2: Extract to temporary directory
            print(f"\n[2/6] Extracting ZIP contents...")
            self.temp_dir = Path(tempfile.mkdtemp(prefix="unzipped_"))
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(self.temp_dir)
            print(f"✓ Extracted to: {self.temp_dir}")
            
            # Step 3: Identify top-level projects and loose files
            print(f"\n[3/6] Identifying projects (top-level directories)...")
            projects, loose_files = self._identify_projects()
            print(f"✓ Found {len(projects)} project(s): {', '.join(projects.keys())}")
            if loose_files:
                print(f"✓ Found {len(loose_files)} loose file(s) not in any project")
            
            # Step 4: Process each project
            print(f"\n[4/6] Processing each project...")
            project_results = {}
            
            for project_name, project_path in projects.items():
                print(f"\n  📁 Processing project: {project_name}")
                project_results[project_name] = self._process_project(project_name, project_path)
            
            # Step 4b: Process loose files if any exist
            if loose_files:
                print(f"\n  📂 Processing miscellaneous files...")
                misc_result = self._process_loose_files(loose_files)
                project_results['_misc_files'] = misc_result
            
            # Step 5: Build final result
            print(f"\n[5/6] Compiling results...")
            result = {
                "zip_metadata": {
                    "root_name": zip_index.root_name,
                    "file_count": zip_index.file_count,
                    "total_uncompressed_bytes": zip_index.total_uncompressed_bytes,
                    "total_compressed_bytes": zip_index.total_compressed_bytes,
                },
                "projects": project_results
            }

            # Optional persistence to SQLite insights store
            if self.insights_store:
                print(f"\n[5b/6] Persisting insights to database...")
                self._persist_insights(zip_path, result)
            
            # Step 6: Print summary
            print(f"\n[6/6] Generating summary...")
            self._print_summary(result)
            
            return result
            
        finally:
            # Always clean up temp directory
            if self.temp_dir and self.temp_dir.exists():
                print(f"\n🧹 Cleaning up temporary directory...")
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _identify_projects(self) -> tuple[Dict[str, Path], List[Path]]:
        """
        Identify top-level directories as individual projects and collect loose files
        
        Handles common ZIP structures where extraction creates a wrapper folder.
        For example, if demo_projects.zip extracts to:
          temp_dir/demo_projects/project-mobile/
          temp_dir/demo_projects/project-webapp/
          temp_dir/demo_projects/notes.txt
        
        We want to identify project-mobile and project-webapp as projects,
        and notes.txt as a loose file.
        
        Returns:
            Tuple of (projects dict, loose files list)
            - projects: Dictionary mapping project name to project path
            - loose_files: List of file paths that aren't in any project
        """
        projects = {}
        loose_files = []
        
        if not self.temp_dir or not self.temp_dir.exists():
            return projects, loose_files
        
        # Get all top-level items in the extracted directory
        top_level_dirs = []
        top_level_files = []
        
        for item in self.temp_dir.iterdir():
            # Skip hidden files and macOS metadata
            if item.name.startswith('.') or item.name.startswith('__MACOSX'):
                continue
            if item.is_dir():
                top_level_dirs.append(item)
            elif item.is_file():
                top_level_files.append(item)
        
        # Case 1: No directories found - treat temp_dir as single project
        if not top_level_dirs:
            projects['root'] = self.temp_dir
            return projects, []
        
        # Case 2: Exactly one top-level directory (likely a wrapper folder from ZIP)
        # Check if it contains subdirectories that should be treated as projects
        if len(top_level_dirs) == 1:
            wrapper_dir = top_level_dirs[0]
            subdirs = []
            wrapper_files = []
            
            # Look for subdirectories and files inside the wrapper
            for item in wrapper_dir.iterdir():
                if item.name.startswith('.') or item.name.startswith('__MACOSX'):
                    continue
                if item.is_dir():
                    subdirs.append(item)
                elif item.is_file():
                    wrapper_files.append(item)
            
            # If we found subdirectories, use those as projects
            if subdirs:
                for subdir in subdirs:
                    projects[subdir.name] = subdir
                # Files in wrapper become loose files
                loose_files = wrapper_files
            else:
                # No subdirectories, so the wrapper itself is the project
                projects[wrapper_dir.name] = wrapper_dir
                # No loose files in this case
        
        # Case 3: Multiple top-level directories - each is a project
        else:
            for item in top_level_dirs:
                projects[item.name] = item
            # Top-level files become loose files
            loose_files = top_level_files
        
        return projects, loose_files
    
    def _process_loose_files(self, loose_files: List[Path]) -> Dict[str, Any]:
        """
        Process loose files that aren't part of any project
        
        Args:
            loose_files: List of file paths
            
        Returns:
            Dictionary with analysis results for loose files
        """
        result = {
            "project_name": "Miscellaneous Files",
            "is_git_repo": False,
            "git_analysis": None,
            "categorized_contents": {},
            "analysis_results": {}
        }
        
        print(f"     ℹ️  Processing {len(loose_files)} loose files")
        
        # Manually categorize loose files by examining each one
        categorized = {
            "code": [],
            "code_by_language": {},
            "documentation": [],
            "images": [],
            "sketches": [],
            "other": []
        }
        
        from src.categorize.file_categorizer import categorize_file, _get_language
        
        for file_path in loose_files:
            file_str = str(file_path)
            category = categorize_file(file_path.name)
            
            if category == "code":
                lang = _get_language(file_path.name) or "unknown"
                categorized["code"].append(file_str)
                categorized["code_by_language"].setdefault(lang, []).append(file_str)
            else:
                categorized[category].append(file_str)
        
        result["categorized_contents"] = categorized
        
        # Count files by type
        code_count = len(categorized.get('code', []))
        doc_count = len(categorized.get('documentation', []))
        img_count = len(categorized.get('images', []))
        print(f"     ✓ Categorized: {code_count} code, {doc_count} docs, {img_count} images")
        
        # Analyze files with appropriate analyzers
        print(f"     🔬 Running file analyzers...")
        try:
            analysis_results = self._analyze_categorized_files(categorized)
            result["analysis_results"] = analysis_results
            print(f"     ✓ Analysis complete")
        except Exception as e:
            print(f"     ✗ Error during analysis: {e}")
            result["analysis_results"] = {"error": str(e)}
        
        return result
    
    def _process_project(self, project_name: str, project_path: Path) -> Dict[str, Any]:
        """
        Process a single project: check Git status, categorize, and analyze
        
        Args:
            project_name: Name of the project
            project_path: Path to the project directory
            
        Returns:
            Dictionary with project analysis results
        """
        result = {
            "project_name": project_name,
            "project_path": str(project_path),
            "is_git_repo": False,
            "git_analysis": None,
            "categorized_contents": {},
            "analysis_results": {}
        }
        
        # Check if this is a Git repository
        git_dir = project_path / ".git"
        is_git = git_dir.exists() and git_dir.is_dir()
        result["is_git_repo"] = is_git
        
        if is_git:
            print(f"     🔍 Git repository detected")
            print(f"     📊 Running Git analysis...")
            try:
                # Run git analysis - we'll analyze all contributors
                git_analysis = self._analyze_git_project(project_path)
                result["git_analysis"] = git_analysis
                
                # Print appropriate message based on results
                if git_analysis.get('total_commits', 0) > 0:
                    contributors = git_analysis.get('total_contributors', 0)
                    print(f"     ✓ Git analysis complete ({git_analysis['total_commits']} commits, {contributors} contributors)")
                else:
                    message = git_analysis.get('message', 'No commits found')
                    print(f"     ℹ️  {message}")
            except Exception as e:
                print(f"     ⚠️  Warning: Git analysis failed: {e}")
                result["git_analysis"] = {"error": str(e)}
        else:
            print(f"     ℹ️  Not a Git repository")
        
        # Categorize files in this project
        print(f"     📁 Categorizing files...")
        try:
            categorized_contents = categorize_folder_structure(str(project_path))
            result["categorized_contents"] = categorized_contents
            
            # Count files by type
            code_count = len(categorized_contents.get('code', []))
            doc_count = len(categorized_contents.get('documentation', []))
            img_count = len(categorized_contents.get('images', []))
            print(f"     ✓ Categorized: {code_count} code, {doc_count} docs, {img_count} images")
        except Exception as e:
            print(f"     ✗ Error categorizing files: {e}")
            result["categorized_contents"] = {"error": str(e)}
            return result
        
        # Analyze files with appropriate analyzers
        print(f"     🔬 Running file analyzers...")
        try:
            analysis_results = self._analyze_categorized_files(categorized_contents)
            result["analysis_results"] = analysis_results
            print(f"     ✓ Analysis complete")
        except Exception as e:
            print(f"     ✗ Error during analysis: {e}")
            result["analysis_results"] = {"error": str(e)}
        
        return result
    
    def _analyze_git_project(self, project_path: Path) -> Dict[str, Any]:
        """
        Analyze Git repository to extract contribution metrics
        
        Args:
            project_path: Path to the Git repository
            
        Returns:
            Dictionary with Git analysis results
        """
        from src.git._git_utils import iter_commits
        
        # Get all commits to identify contributors
        try:
            all_commits = list(iter_commits(project_path))
        except Exception as e:
            return {
                "total_commits": 0,
                "contributors": [],
                "message": f"Unable to read Git history: {str(e)}"
            }
        
        if not all_commits:
            return {
                "total_commits": 0,
                "contributors": [],
                "message": "Git repository is empty (no commits yet)"
            }
        
        # Identify unique contributors
        contributors_set = set()
        for commit in all_commits:
            contributors_set.add((commit["author_name"], commit["author_email"]))
        
        # Analyze each contributor
        contributor_analyses = []
        for name, email in contributors_set:
            try:
                # Use email as identifier (preferred)
                contrib_summary = summarize_author_contrib(
                    project_path,
                    email,
                    prefer_email=True,
                    fuzzy=False
                )
                contributor_analyses.append(contrib_summary)
            except Exception as e:
                print(f"        ⚠️  Could not analyze contributor {name}: {e}")
                continue
        
        # Sort contributors by commit count
        contributor_analyses.sort(key=lambda x: x["commits"], reverse=True)
        
        return {
            "total_commits": len(all_commits),
            "total_contributors": len(contributor_analyses),
            "contributors": contributor_analyses
        }
    
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

    def _persist_insights(self, zip_path: Path, payload: Dict[str, Any]) -> None:
        """Persist pipeline output to the configured insights store."""
        if not self.insights_store:
            return
        try:
            stats = self.insights_store.record_pipeline_run(
                str(zip_path),
                payload,
                pipeline_version="artifact-pipeline/v1",
            )
            print(
                f"     ✓ Stored insights ({stats.project_count} projects, "
                f"{stats.inserted} inserted / {stats.updated} updated / {stats.deleted} deleted)"
            )
        except Exception as exc:
            print(f"     ⚠️  Warning: Unable to persist insights: {exc}")
    
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
        
        # Projects summary
        projects = result.get('projects', {})
        regular_projects = {k: v for k, v in projects.items() if k != '_misc_files'}
        misc_files = projects.get('_misc_files')
        
        print(f"\n📦 Projects Found: {len(regular_projects)}")
        if misc_files:
            print(f"📂 Miscellaneous Files: Yes ({len(misc_files.get('categorized_contents', {}).get('code', []) + misc_files.get('categorized_contents', {}).get('documentation', []) + misc_files.get('categorized_contents', {}).get('images', []))} loose files)")
        
        for project_name, project_data in regular_projects.items():
            print(f"\n{'─'*70}")
            print(f"📁 Project: {project_name}")
            print(f"{'─'*70}")
            
            # Git status
            is_git = project_data.get('is_git_repo', False)
            if is_git:
                print(f"   🔍 Git Repository: YES")
                git_analysis = project_data.get('git_analysis', {})
                if git_analysis and 'error' not in git_analysis:
                    print(f"      • Total commits: {git_analysis.get('total_commits', 0)}")
                    print(f"      • Contributors: {git_analysis.get('total_contributors', 0)}")
                    
                    # Show top 3 contributors
                    contributors = git_analysis.get('contributors', [])
                    if contributors:
                        print(f"      • Top contributors:")
                        for i, contrib in enumerate(contributors[:3], 1):
                            author = contrib.get('author', {})
                            commits = contrib.get('commits', 0)
                            print(f"         {i}. {author.get('name', 'Unknown')} ({commits} commits)")
            else:
                print(f"   🔍 Git Repository: NO")
            
            # Categorization summary
            categorized = project_data.get('categorized_contents', {})
            if categorized and 'error' not in categorized:
                print(f"\n   📁 File Categorization:")
                print(f"      • Code files: {len(categorized.get('code', []))}")
                
                # Show languages breakdown
                code_by_lang = categorized.get('code_by_language', {})
                if code_by_lang:
                    print(f"        Languages detected:")
                    for lang, files in sorted(code_by_lang.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
                        print(f"          - {lang}: {len(files)} files")
                
                print(f"      • Documentation files: {len(categorized.get('documentation', []))}")
                print(f"      • Image files: {len(categorized.get('images', []))}")
                print(f"      • Video files: {len([f for f in categorized.get('other', []) if Path(f).suffix.lower() in self.VIDEO_EXTENSIONS])}")
            
            # Analysis summary
            analysis = project_data.get('analysis_results', {})
            if analysis and 'error' not in analysis:
                print(f"\n   🔬 Analysis Results:")
                
                # Documentation analysis
                doc_analysis = analysis.get('documentation')
                if doc_analysis and doc_analysis is not None and 'error' not in doc_analysis:
                    totals = doc_analysis.get('totals', {})
                    print(f"      • Documentation: {totals.get('total_files', 0)} files, {totals.get('total_words', 0):,} words")
                
                # Image analysis
                img_analysis = analysis.get('images')
                if img_analysis and img_analysis is not None and 'error' not in img_analysis:
                    total_size = sum(img.get('file_stats', {}).get('size_mb', 0) for img in img_analysis)
                    print(f"      • Images: {len(img_analysis)} files, {total_size:.2f} MB")
                
                # Code analysis
                code_analysis = analysis.get('code')
                if code_analysis and code_analysis is not None and 'error' not in code_analysis:
                    metrics = code_analysis.get('metrics', {})
                    print(f"      • Code: {metrics.get('total_files', 0)} files, {metrics.get('total_lines', 0):,} lines")
                    langs = metrics.get('languages', [])
                    if langs:
                        print(f"        Languages: {', '.join(langs)}")
                
                # Video analysis
                video_analysis = analysis.get('videos')
                if video_analysis and video_analysis is not None and 'error' not in video_analysis:
                    metrics = video_analysis.get('metrics', {})
                    duration = metrics.get('total_duration', 0)
                    print(f"      • Videos: {metrics.get('total_videos', 0)} files, {duration:.1f}s duration")
        
        # Miscellaneous files summary
        if misc_files:
            print(f"\n{'─'*70}")
            print(f"📂 Miscellaneous Files (not in any project)")
            print(f"{'─'*70}")
            
            # Categorization summary
            categorized = misc_files.get('categorized_contents', {})
            if categorized:
                print(f"\n   📁 File Categorization:")
                print(f"      • Code files: {len(categorized.get('code', []))}")
                
                code_by_lang = categorized.get('code_by_language', {})
                if code_by_lang:
                    print(f"        Languages detected:")
                    for lang, files in sorted(code_by_lang.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
                        print(f"          - {lang}: {len(files)} files")
                
                print(f"      • Documentation files: {len(categorized.get('documentation', []))}")
                print(f"      • Image files: {len(categorized.get('images', []))}")
                print(f"      • Video files: {len([f for f in categorized.get('other', []) if Path(f).suffix.lower() in self.VIDEO_EXTENSIONS])}")
            
            # Analysis summary
            analysis = misc_files.get('analysis_results', {})
            if analysis:
                print(f"\n   🔬 Analysis Results:")
                
                doc_analysis = analysis.get('documentation')
                if doc_analysis and 'error' not in doc_analysis:
                    totals = doc_analysis.get('totals', {})
                    print(f"      • Documentation: {totals.get('total_files', 0)} files, {totals.get('total_words', 0):,} words")
                
                img_analysis = analysis.get('images')
                if img_analysis and 'error' not in img_analysis:
                    total_size = sum(img.get('file_stats', {}).get('size_mb', 0) for img in img_analysis)
                    print(f"      • Images: {len(img_analysis)} files, {total_size:.2f} MB")
                
                code_analysis = analysis.get('code')
                if code_analysis and 'error' not in code_analysis:
                    metrics = code_analysis.get('metrics', {})
                    print(f"      • Code: {metrics.get('total_files', 0)} files, {metrics.get('total_lines', 0):,} lines")
                
                video_analysis = analysis.get('videos')
                if video_analysis and 'error' not in video_analysis:
                    metrics = video_analysis.get('metrics', {})
                    print(f"      • Videos: {metrics.get('total_videos', 0)} files, {metrics.get('total_duration', 0):.1f}s duration")
        
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
        
        # Print detailed analysis results by project
        print("\n" + "="*70)
        print("📋 DETAILED ANALYSIS RESULTS BY PROJECT")
        print("="*70)
        
        projects = result.get('projects', {})
        
        # Separate regular projects from misc files
        regular_projects = {k: v for k, v in projects.items() if k != '_misc_files'}
        misc_files = projects.get('_misc_files')
        
        # Process regular projects first
        for project_name, project_data in regular_projects.items():
            print("\n" + "="*70)
            print(f"PROJECT: {project_name}")
            print("="*70)
            
            # Git Analysis
            if project_data.get('is_git_repo'):
                git_analysis = project_data.get('git_analysis', {})
                print("\n" + "-"*70)
                print("🔍 GIT ANALYSIS")
                print("-"*70)
                if git_analysis:
                    if 'error' in git_analysis:
                        print(f"Error: {git_analysis['error']}")
                    else:
                        print(json.dumps(git_analysis, indent=2))
                else:
                    print("No Git analysis data available")
            
            # File Analysis Results
            analysis = project_data.get('analysis_results', {})
            
            print("\n" + "-"*70)
            print("📄 DOCUMENTATION ANALYSIS")
            print("-"*70)
            doc_data = analysis.get('documentation')
            if doc_data is None:
                print("No documentation files to analyze")
            elif isinstance(doc_data, dict) and 'error' in doc_data:
                print(f"Error: {doc_data['error']}")
            else:
                print(json.dumps(doc_data, indent=2))
            
            print("\n" + "-"*70)
            print("🖼️  IMAGE ANALYSIS")
            print("-"*70)
            img_data = analysis.get('images')
            if img_data is None:
                print("No image files to analyze")
            elif isinstance(img_data, dict) and 'error' in img_data:
                print(f"Error: {img_data['error']}")
            elif img_data:
                # Print summary for each image (full output can be very large)
                for i, img in enumerate(img_data, 1):
                    print(f"\n[Image {i}] {img.get('file_name', 'unknown')}")
                    print(f"  Resolution: {img.get('resolution', {}).get('width', 0)}x{img.get('resolution', {}).get('height', 0)}")
                    print(f"  Size: {img.get('file_stats', {}).get('size_mb', 0):.2f} MB")
                    print(f"  Format: {img.get('format', {}).get('format', 'unknown')}")
                    content = img.get('content_classification', {})
                    print(f"  Type: {content.get('primary_type', 'unknown')}")
            else:
                print("No image files found")
            
            print("\n" + "-"*70)
            print("💻 CODE ANALYSIS")
            print("-"*70)
            code_data = analysis.get('code')
            if code_data is None:
                print("No code files to analyze")
            elif isinstance(code_data, dict) and 'error' in code_data:
                print(f"Error: {code_data['error']}")
            elif code_data:
                # Print individual file analyses
                files = code_data.get('files', [])
                if files:
                    print(f"Individual File Analysis ({len(files)} files):")
                    print(json.dumps(files, indent=2))
                
                # Print aggregate metrics summary
                metrics = code_data.get('metrics', {})
                print(f"\n{'─'*70}")
                print("Aggregate Metrics Summary:")
                print(json.dumps(metrics, indent=2))
            else:
                print("No code files found")
            
            print("\n" + "-"*70)
            print("🎥 VIDEO ANALYSIS")
            print("-"*70)
            video_data = analysis.get('videos')
            if video_data is None:
                print("No video files to analyze")
            elif isinstance(video_data, dict) and 'error' in video_data:
                print(f"Error: {video_data['error']}")
            elif video_data:
                print(json.dumps(video_data, indent=2))
            else:
                print("No video files found")
        
        # Process miscellaneous files section if it exists
        if misc_files:
            print("\n" + "="*70)
            print(f"MISCELLANEOUS FILES (not in any project)")
            print("="*70)
            
            # File Analysis Results (no Git analysis for loose files)
            analysis = misc_files.get('analysis_results', {})
            
            print("\n" + "-"*70)
            print("📄 DOCUMENTATION ANALYSIS")
            print("-"*70)
            doc_data = analysis.get('documentation')
            if doc_data is None:
                print("No documentation files")
            elif isinstance(doc_data, dict) and 'error' in doc_data:
                print(f"Error: {doc_data['error']}")
            else:
                print(json.dumps(doc_data, indent=2))
            
            print("\n" + "-"*70)
            print("🖼️  IMAGE ANALYSIS")
            print("-"*70)
            img_data = analysis.get('images')
            if img_data is None:
                print("No image files")
            elif isinstance(img_data, dict) and 'error' in img_data:
                print(f"Error: {img_data['error']}")
            elif img_data:
                for i, img in enumerate(img_data, 1):
                    print(f"\n[Image {i}] {img.get('file_name', 'unknown')}")
                    print(f"  Resolution: {img.get('resolution', {}).get('width', 0)}x{img.get('resolution', {}).get('height', 0)}")
                    print(f"  Size: {img.get('file_stats', {}).get('size_mb', 0):.2f} MB")
                    print(f"  Format: {img.get('format', {}).get('format', 'unknown')}")
                    content = img.get('content_classification', {})
                    print(f"  Type: {content.get('primary_type', 'unknown')}")
            else:
                print("No image files")
            
            print("\n" + "-"*70)
            print("💻 CODE ANALYSIS")
            print("-"*70)
            code_data = analysis.get('code')
            if code_data is None:
                print("No code files")
            elif isinstance(code_data, dict) and 'error' in code_data:
                print(f"Error: {code_data['error']}")
            elif code_data:
                files = code_data.get('files', [])
                if files:
                    print(f"Individual File Analysis ({len(files)} files):")
                    print(json.dumps(files, indent=2))
                
                metrics = code_data.get('metrics', {})
                print(f"\n{'─'*70}")
                print("Aggregate Metrics Summary:")
                print(json.dumps(metrics, indent=2))
            else:
                print("No code files")
            
            print("\n" + "-"*70)
            print("🎥 VIDEO ANALYSIS")
            print("-"*70)
            video_data = analysis.get('videos')
            if video_data is None:
                print("No video files")
            elif isinstance(video_data, dict) and 'error' in video_data:
                print(f"Error: {video_data['error']}")
            elif video_data:
                print(json.dumps(video_data, indent=2))
            else:
                print("No video files")
        
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
