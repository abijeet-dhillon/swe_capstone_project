#!/usr/bin/env python3
"""
Rank projects by importance based on user contributions.
Retrieves projects from database and ranks them using various criteria.
"""
import sys
import argparse
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from insights.storage import ProjectInsightsStore
from project.aggregator import ProjectInfo, from_git, from_local
from project.top_summary import rank_projects, generate_summaries, to_format, RankingCriteria


def load_project_info_from_storage(store: ProjectInsightsStore) -> List[ProjectInfo]:
    """
    Load all projects from database and convert to ProjectInfo objects.
    
    Args:
        store: ProjectInsightsStore instance
        
    Returns:
        List of ProjectInfo objects
    """
    from project.aggregator import compute_rank_inputs, compute_preliminary_score
    
    project_infos = []
    projects = store.list_all_projects()
    
    for proj in projects:
        project_id = proj['id']
        project_name = proj['project_name']
        
        # Skip _misc_files
        if project_name == '_misc_files':
            continue
        
        try:
            # Load project insight payload
            payload = store.load_project_insight_by_id(project_id)
            if not payload:
                print(f"   ⚠️  No payload for project {project_name} (ID: {project_id})")
                continue
            
            # Try to get project_metrics first (if stored as ProjectInfo dict)
            project_metrics = payload.get('project_metrics', {})
            
            # If project_metrics exists and has all required fields, use it directly
            if project_metrics and isinstance(project_metrics, dict):
                if all(key in project_metrics for key in ['name', 'duration', 'totals']):
                    try:
                        pi = ProjectInfo(
                            id=project_metrics.get('id', str(project_id)),
                            name=project_metrics.get('name', project_name),
                            source=project_metrics.get('source', 'merged'),
                            duration=project_metrics.get('duration', {}),
                            is_collaborative=project_metrics.get('is_collaborative', False),
                            authors=project_metrics.get('authors', []),
                            languages=project_metrics.get('languages', []),
                            frameworks=project_metrics.get('frameworks', []),
                            skills=project_metrics.get('skills', []),
                            activity_mix=project_metrics.get('activity_mix', {"code": 0, "test": 0, "doc": 0}),
                            lines_of_code=project_metrics.get('lines_of_code', 0),
                            totals=project_metrics.get('totals', {"files": 0, "commits": 0}),
                            notes=project_metrics.get('notes', []),
                            rank_inputs=project_metrics.get('rank_inputs', {}),
                            preliminary_score=project_metrics.get('preliminary_score', 0.0),
                        )
                        # Ensure rank inputs and score are computed
                        if not pi.rank_inputs:
                            pi.rank_inputs = compute_rank_inputs(pi)
                        if not pi.preliminary_score:
                            pi.preliminary_score = compute_preliminary_score(pi.rank_inputs)
                        project_infos.append(pi)
                        continue
                    except Exception as e:
                        pass  # Fall through to reconstruction logic
            
            # Reconstruct ProjectInfo from payload data (same logic as orchestrator)
            git_analysis = payload.get('git_analysis', {})
            code_analysis = payload.get('analysis_results', {}).get('code', {})
            
            # Extract duration info from git analysis
            duration_info = {"start": None, "end": None, "days": 0}
            if isinstance(git_analysis, dict) and ("error" not in git_analysis):
                if "first_commit_at" in git_analysis:
                    duration_info = {
                        "start": git_analysis.get("first_commit_at"),
                        "end": git_analysis.get("last_commit_at"),
                        "days": git_analysis.get("duration_days", 0)
                    }
            
            # Determine if collaborative
            is_collaborative = False
            if payload.get("is_git_repo") and git_analysis:
                is_collaborative = git_analysis.get("total_contributors", 0) > 1
            else:
                # Fallback to project_metrics
                is_collaborative = project_metrics.get('is_collaborative', False) if project_metrics else False
            
            # Extract contributors
            authors = []
            if git_analysis and "contributors" in git_analysis:
                for contrib in git_analysis.get("contributors", []):
                    author_info = contrib.get("author", {})
                    authors.append({
                        "name": author_info.get("name", "Unknown"),
                        "email": author_info.get("email", ""),
                        "commits": contrib.get("commits", 0)
                    })
            
            # Extract languages and frameworks from code_analysis or project_metrics
            languages = []
            frameworks = []
            if code_analysis and isinstance(code_analysis, dict) and "error" not in code_analysis:
                metrics = code_analysis.get("metrics", {})
                languages = metrics.get("languages", [])
                frameworks = metrics.get("frameworks", [])
            elif project_metrics:
                languages = project_metrics.get('languages', [])
                frameworks = project_metrics.get('frameworks', [])
            
            # Extract skills
            skills = []
            if code_analysis and isinstance(code_analysis, dict) and "error" not in code_analysis:
                skill_data = code_analysis.get("skill_analysis", {})
                if skill_data:
                    aggregate = skill_data.get("aggregate", {})
                    skills = aggregate.get("advanced_skills", [])
            elif project_metrics:
                skills = project_metrics.get('skills', [])
            
            # Extract activity mix
            activity_mix = {"code": 0, "test": 0, "doc": 0}
            if git_analysis and isinstance(git_analysis, dict) and "error" not in git_analysis:
                activity_mix_raw = git_analysis.get("activity_mix", {})
                if isinstance(activity_mix_raw, dict):
                    # Map activity types
                    activity_mix = {
                        "code": activity_mix_raw.get("feature", 0) + activity_mix_raw.get("refactor", 0),
                        "test": activity_mix_raw.get("test", 0),
                        "doc": activity_mix_raw.get("docs", 0),
                    }
            
            # Extract totals from code_analysis or project_metrics
            total_commits = 0
            total_files = 0
            total_loc = 0
            
            if git_analysis and isinstance(git_analysis, dict) and "error" not in git_analysis:
                total_commits = git_analysis.get("total_commits", 0)
            
            if code_analysis and isinstance(code_analysis, dict) and "error" not in code_analysis:
                metrics = code_analysis.get("metrics", {})
                total_files = metrics.get("total_files", 0)
                total_loc = metrics.get("total_lines", 0)
            elif project_metrics:
                total_files = project_metrics.get('total_files', 0)
                total_loc = project_metrics.get('total_lines', 0)
                if not total_commits:
                    total_commits = project_metrics.get('total_commits', 0)
            
            # Create ProjectInfo
            pi = ProjectInfo(
                id=str(project_id),
                name=project_name,
                source="merged",
                duration=duration_info,
                is_collaborative=is_collaborative,
                authors=authors,
                languages=languages,
                frameworks=frameworks,
                skills=skills,
                activity_mix=activity_mix,
                lines_of_code=total_loc,
                totals={"files": total_files, "commits": total_commits},
                notes=[],
                rank_inputs={},
                preliminary_score=0.0
            )
            
            # Compute ranking metrics
            pi.rank_inputs = compute_rank_inputs(pi)
            pi.preliminary_score = compute_preliminary_score(pi.rank_inputs)
            
            project_infos.append(pi)
            
        except Exception as e:
            import traceback
            print(f"⚠️  Warning: Error loading project {project_name}: {e}")
            if project_name in ['project-mobile', 'project-webapp']:
                print(f"   Debug traceback:")
                traceback.print_exc()
            continue
    
    return project_infos


def rank_and_display(
    store: ProjectInsightsStore,
    n: int = 5,
    criteria: RankingCriteria = "score",
    format_output: str = "text"
):
    """
    Rank projects and display results.
    
    Args:
        store: ProjectInsightsStore instance
        n: Number of top projects to show
        criteria: Ranking criteria (score, recency, commits, loc, impact)
        format_output: Output format (text, json, csv)
    """
    print("=" * 70)
    print("🏆 PROJECT RANKING BY USER CONTRIBUTIONS")
    print("=" * 70)
    
    # Load projects
    print(f"\n[1/2] Loading projects from database...")
    all_projects = store.list_all_projects()
    print(f"   Found {len(all_projects)} project(s) in database")
    project_infos = load_project_info_from_storage(store)
    
    if not project_infos:
        print("❌ No projects found in database.")
        print("\nTo add projects, run:")
        print("  python3 test_repository_analysis.py --repo <path>")
        print("  or")
        print("  python3 -m src.pipeline.orchestrator <path/to/project.zip>")
        return
    
    print(f"   ✓ Loaded {len(project_infos)} project(s)")
    
    # Rank projects
    print(f"\n[2/2] Ranking projects by '{criteria}' criteria...")
    ranked = rank_projects(project_infos, n=n, criteria=criteria)
    
    if not ranked:
        print("❌ No projects could be ranked.")
        return
    
    print(f"   ✓ Ranked {len(ranked)} top project(s)")
    
    # Generate summaries
    summaries = generate_summaries(project_infos, n=n, criteria=criteria)
    
    # Display results
    print("\n" + "=" * 70)
    print(f"TOP {len(ranked)} RANKED PROJECTS")
    print("=" * 70)
    
    if format_output == "json":
        print(to_format(summaries, fmt="json"))
    elif format_output == "csv":
        print(to_format(summaries, fmt="csv"))
    else:  # text format
        print(to_format(summaries, fmt="text"))
    
    print("\n" + "=" * 70)
    print(f"Ranking Criteria: {criteria}")
    print(f"Total Projects Analyzed: {len(project_infos)}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Rank projects by importance based on user contributions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rank top 5 projects by score (default)
  python3 rank_projects.py
  
  # Rank top 3 projects by recency
  python3 rank_projects.py --top 3 --criteria recency
  
  # Rank by commits
  python3 rank_projects.py --criteria commits
  
  # Output as JSON
  python3 rank_projects.py --format json
  
  # Output as CSV
  python3 rank_projects.py --format csv
        """
    )
    
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top projects to show (default: 5)"
    )
    
    parser.add_argument(
        "--criteria",
        choices=["score", "recency", "commits", "loc", "impact"],
        default="score",
        help="Ranking criteria (default: score)"
    )
    
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--db-path",
        help="Override database path"
    )
    
    args = parser.parse_args()
    
    # Initialize store
    store = ProjectInsightsStore(db_path=args.db_path) if args.db_path else ProjectInsightsStore()
    
    # Rank and display
    rank_and_display(
        store=store,
        n=args.top,
        criteria=args.criteria,
        format_output=args.format
    )


if __name__ == "__main__":
    main()

