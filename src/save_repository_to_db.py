#!/usr/bin/env python3
"""
Save repository analysis results to the database.
Converts repository analysis format to pipeline format and stores it.
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from services.repository_analysis_service import RepositoryAnalysisService
from insights.storage import ProjectInsightsStore
from project.aggregator import from_git, to_dict
from git.project_git_analyzer import analyze_project_repo


def convert_repo_analysis_to_pipeline_format(
    repo_path: str,
    analysis_results: dict
) -> dict:
    """
    Convert repository analysis results to pipeline format for storage.
    
    Args:
        repo_path: Path to the repository
        analysis_results: Results from RepositoryAnalysisService
        
    Returns:
        Dictionary in pipeline format
    """
    # Safely get repository data
    repo_data = analysis_results.get('repository_analysis') or {}
    if not isinstance(repo_data, dict):
        repo_data = {}
    
    repo_name = Path(repo_path).name
    
    # Safely get contributors
    contributors = repo_data.get('contributors') or []
    if not isinstance(contributors, list):
        contributors = []
    
    # Get first and last commit dates safely
    first_commit = ''
    last_commit = ''
    if contributors and len(contributors) > 0:
        first_contributor = contributors[0] if isinstance(contributors[0], dict) else {}
        first_commit = first_contributor.get('first_commit', '') or ''
        last_commit = first_contributor.get('last_commit', '') or ''
    
    # Get project metrics using aggregator
    try:
        git_metrics_raw = analyze_project_repo(Path(repo_path))
        
        # Convert analyze_project_repo format to from_git expected format
        git_metrics = {
            "authors": git_metrics_raw.get("authors", []),
            "is_collaborative": git_metrics_raw.get("project_type") == "collaborative",
            "duration": {
                "first_commit_iso": git_metrics_raw.get("first_commit_at", ""),
                "last_commit_iso": git_metrics_raw.get("last_commit_at", ""),
                "days": git_metrics_raw.get("duration_days", 0),
            },
            "commits": git_metrics_raw.get("total_commits", 0),
            "files_touched": 0,  # Not available from analyze_project_repo
            "by_activity": {
                # Map activity_mix to by_activity format
                "code": git_metrics_raw.get("activity_mix", {}).get("feature", 0) + 
                        git_metrics_raw.get("activity_mix", {}).get("refactor", 0),
                "test": git_metrics_raw.get("activity_mix", {}).get("test", 0),
                "doc": git_metrics_raw.get("activity_mix", {}).get("docs", 0),
            },
            "languages": [],  # Not available from analyze_project_repo
            "lines_of_code": 0,  # Not available from analyze_project_repo
            "notes": [],
        }
        
        project_info = from_git(repo_path, git_metrics)
        project_dict = to_dict(project_info)
    except Exception as e:
        print(f"⚠️  Warning: Could not generate project metrics: {e}")
        import traceback
        traceback.print_exc()
        project_dict = {
            "name": repo_name,
            "languages": [],
            "frameworks": [],
            "is_collaborative": repo_data.get('contributor_count', 0) > 1,
            "totals": {"commits": repo_data.get('total_commits', 0)},
            "duration": {}
        }
    
    # Safely get file extensions
    file_extensions = repo_data.get('file_extensions') or {}
    if not isinstance(file_extensions, dict):
        file_extensions = {}
    
    # Safely get AI insights
    ai_insights = analysis_results.get('ai_insights') or {}
    if not isinstance(ai_insights, dict):
        ai_insights = {}
    
    # Create pipeline format
    pipeline_result = {
        "zip_metadata": {
            "root_name": repo_name,
            "file_count": 0,  # Not available from repo analysis
            "total_uncompressed_bytes": 0,
            "total_compressed_bytes": 0,
        },
        "projects": {
            repo_name: {
                "project_path": repo_path,
                "is_git_repo": True,
                "git_analysis": {
                    "total_commits": repo_data.get('total_commits', 0) or 0,
                    "contributor_count": repo_data.get('contributor_count', 0) or 0,
                    "first_commit_at": first_commit,
                    "last_commit_at": last_commit,
                },
                "analysis_results": {
                    "code": {
                        "metrics": {
                            "total_files": len(file_extensions),
                            "languages": list(file_extensions.keys()) if file_extensions else [],
                        }
                    }
                },
                "project_metrics": project_dict,
                "portfolio_item": ai_insights.get('portfolio_item') or {},
                "resume_item": ai_insights.get('resume_item') or {},
            }
        },
        "extras": {}
    }
    
    return pipeline_result


def save_repository_analysis(
    repo_path: str,
    analyze_code_quality: bool = True,
    generate_ai_summary: bool = False,
    db_path: str = None
):
    """
    Analyze a repository and save results to database.
    
    Args:
        repo_path: Path to Git repository
        analyze_code_quality: Whether to analyze code quality
        generate_ai_summary: Whether to generate AI summaries
        db_path: Optional database path
    """
    print("=" * 70)
    print("SAVING REPOSITORY ANALYSIS TO DATABASE")
    print("=" * 70)
    
    # Analyze repository
    print(f"\n[1/2] Analyzing repository: {repo_path}")
    service = RepositoryAnalysisService(api_key=None)
    results = service.analyze_repository(
        repo_path,
        analyze_code_quality=analyze_code_quality,
        generate_ai_summary=generate_ai_summary
    )
    
    # Convert to pipeline format
    print(f"\n[2/2] Converting and saving to database...")
    pipeline_result = convert_repo_analysis_to_pipeline_format(repo_path, results)
    
    # Save to database
    store = ProjectInsightsStore(db_path=db_path) if db_path else ProjectInsightsStore()
    
    # Use repo path as "zip_path" for storage (it's just an identifier)
    stats = store.record_pipeline_run(
        zip_path=repo_path,
        pipeline_result=pipeline_result,
        pipeline_version="repository-analysis/v1"
    )
    
    print("\n" + "=" * 70)
    print("✅ SAVED TO DATABASE")
    print("=" * 70)
    print(f"Projects stored: {stats.project_count}")
    print(f"Inserted: {stats.inserted}")
    print(f"Updated: {stats.updated}")
    print(f"Deleted: {stats.deleted}")
    print("\nUse 'python3 retrieve_project_by_id.py --list' to see stored projects")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a Git repository and save results to database."
    )
    parser.add_argument(
        "repo_path",
        help="Path to Git repository"
    )
    parser.add_argument(
        "--no-code-quality",
        action="store_true",
        help="Skip code quality analysis"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Enable AI summarization (requires OPENAI_API_KEY)"
    )
    parser.add_argument(
        "--db-path",
        help="Override database path"
    )
    
    args = parser.parse_args()
    
    save_repository_analysis(
        repo_path=args.repo_path,
        analyze_code_quality=not args.no_code_quality,
        generate_ai_summary=args.ai,
        db_path=args.db_path
    )


if __name__ == "__main__":
    main()

