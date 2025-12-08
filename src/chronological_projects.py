#!/usr/bin/env python3
"""
chronological_projects.py
---
Generates a chronological timeline of projects from the database,
ordered by project start date or creation date.
"""

import sys
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

sys.path.insert(0, str(Path(__file__).parent))

from insights.storage import ProjectInsightsStore
from project.aggregator import ProjectInfo, compute_rank_inputs, compute_preliminary_score


def load_project_info_from_storage(store: ProjectInsightsStore) -> List[tuple]:
    """
    Load all projects from database and convert to ProjectInfo objects.
    Returns list of tuples: (ProjectInfo, created_at_datetime)
    """
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
            
            # Reconstruct ProjectInfo from payload data
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
            
            # Fallback: Use database creation date if no Git data
            if not duration_info.get("start") and not duration_info.get("end"):
                # Use project creation date from database as fallback
                created_at_str = proj.get('created_at')
                if created_at_str:
                    try:
                        # Parse the created_at timestamp
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        # Use creation date as both start and end (single-day project)
                        duration_info = {
                            "start": created_at.isoformat(),
                            "end": created_at.isoformat(),
                            "days": 0
                        }
                    except (ValueError, AttributeError):
                        pass
            
            # Determine if collaborative
            is_collaborative = False
            if payload.get("is_git_repo") and git_analysis:
                is_collaborative = git_analysis.get("total_contributors", 0) > 1
            else:
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
            
            # Extract languages and frameworks
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
                    activity_mix = {
                        "code": activity_mix_raw.get("feature", 0) + activity_mix_raw.get("refactor", 0),
                        "test": activity_mix_raw.get("test", 0),
                        "doc": activity_mix_raw.get("docs", 0),
                    }
            
            # Extract totals
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
            
            # Get created_at timestamp
            created_at = None
            created_at_str = proj.get('created_at')
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            
            project_infos.append((pi, created_at))
            
        except Exception as e:
            continue
    
    return project_infos


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        # Try ISO format first
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Try YYYY-MM-DD format
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def build_chronological_project_list_from_directory(
    directory_path: str,
    sort_by: str = "start",
    reverse: bool = False
) -> List[Dict[str, Any]]:
    """
    Build chronological list of projects by analyzing a directory.
    
    Args:
        directory_path: Path to directory containing projects
        sort_by: Sort by "start" (project start date) or "created" (database creation date)
        reverse: If True, reverse order (newest first)
    
    Returns:
        List of project dictionaries with chronological information
    """
    from analyze.code_analyzer import CodeAnalyzer
    from categorize.file_categorizer import categorize_folder_structure
    
    directory = Path(directory_path)
    if not directory.exists():
        raise ValueError(f"Directory not found: {directory_path}")
    
    # Identify projects (top-level directories)
    projects_dict = {}
    loose_files = []
    
    # Get all top-level items
    top_level_dirs = []
    top_level_files = []
    
    for item in directory.iterdir():
        # Skip hidden files and macOS metadata
        if item.name.startswith('.') or item.name.startswith('__MACOSX'):
            continue
        if item.is_dir():
            top_level_dirs.append(item)
        elif item.is_file():
            top_level_files.append(item)
    
    # Handle wrapper directory case (like demo_projects/demo_projects/project-mobile)
    if len(top_level_dirs) == 1:
        wrapper_dir = top_level_dirs[0]
        subdirs = [d for d in wrapper_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if subdirs:
            # Use subdirectories as projects
            for subdir in subdirs:
                projects_dict[subdir.name] = subdir
        else:
            # Use wrapper as single project
            projects_dict[wrapper_dir.name] = wrapper_dir
    else:
        # Use top-level directories as projects
        for dir_item in top_level_dirs:
            projects_dict[dir_item.name] = dir_item
    
    if not top_level_dirs:
        # No directories, treat root as single project
        projects_dict['root'] = directory
    
    # Analyze each project
    code_analyzer = CodeAnalyzer()
    projects_list = []
    
    for project_name, project_path in projects_dict.items():
        try:
            # Get all files in project directory
            file_dates = []
            code_files = []
            languages = set()
            frameworks = set()
            skills = set()
            total_loc = 0
            
            for file_path in project_path.rglob("*"):
                if file_path.is_file():
                    # Skip hidden and metadata files
                    if file_path.name.startswith('.') or file_path.name.startswith('__MACOSX'):
                        continue
                    if file_path.name.startswith('._') or file_path.name == '.DS_Store':
                        continue
                    
                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        file_dates.append(mtime)
                        
                        # Analyze code files
                        if file_path.suffix.lower() in {'.py', '.js', '.java', '.cpp', '.c', '.ts', '.rb', '.go', '.rs', '.swift', '.kt', '.m'}:
                            code_files.append(str(file_path))
                            try:
                                analysis = code_analyzer.analyze_file(str(file_path))
                                if analysis.language:
                                    languages.add(analysis.language)
                                if analysis.frameworks:
                                    frameworks.update(analysis.frameworks)
                                # Skills from code analyzer are language-based, use advanced skill extractor for real skills
                                if hasattr(analysis, 'skills') and analysis.skills:
                                    # Filter out language names from skills
                                    actual_skills = [s for s in analysis.skills if s.lower() not in [l.lower() for l in languages]]
                                    skills.update(actual_skills)
                                total_loc += analysis.lines_of_code
                            except Exception:
                                pass
                    except (OSError, ValueError):
                        continue
            
            if not file_dates:
                continue
            
            # Calculate project period from file modification dates
            start_date = min(file_dates)
            end_date = max(file_dates)
            duration_days = (end_date - end_date).days if start_date == end_date else (end_date - start_date).days
            
            # Create ProjectInfo-like object
            project_info = {
                "id": project_name,
                "name": project_name,
                "source": "local",
                "duration": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": max(0, duration_days)
                },
                "is_collaborative": False,  # Can't determine from files alone
                "authors": [],
                "languages": sorted(languages),
                "frameworks": sorted(frameworks),
                "skills": sorted(skills),
                "activity_mix": {"code": len(code_files), "test": 0, "doc": 0},
                "lines_of_code": total_loc,
                "totals": {"files": len(file_dates), "commits": 0},
                "notes": [],
                "rank_inputs": {},
                "preliminary_score": 0.0
            }
            
            # Create a simple ProjectInfo-like dict
            projects_list.append({
                "project": project_info,
                "sort_date": start_date if sort_by == "start" else end_date,
                "start_date": start_date,
                "end_date": end_date,
            })
            
        except Exception as e:
            print(f"   ⚠️  Warning: Could not analyze project {project_name}: {e}")
            continue
    
    # Sort by date
    projects_list.sort(key=lambda x: x["sort_date"], reverse=reverse)
    
    return projects_list


def build_chronological_project_list(
    store: ProjectInsightsStore,
    sort_by: str = "start",
    reverse: bool = False
) -> List[Dict[str, Any]]:
    """
    Build chronological list of projects from database.
    
    Args:
        store: ProjectInsightsStore instance
        sort_by: Sort by "start" (project start date) or "created" (database creation date)
        reverse: If True, reverse order (newest first)
    
    Returns:
        List of project dictionaries with chronological information
    """
    project_data = load_project_info_from_storage(store)
    
    # Convert to list of dicts with sortable dates
    projects_list = []
    for pi, created_at in project_data:
        # Get sort date
        if sort_by == "start":
            sort_date = parse_date(pi.duration.get("start"))
            if not sort_date:
                # Fallback to end date, then created_at, then current date
                sort_date = parse_date(pi.duration.get("end")) or created_at or datetime.now()
        else:  # sort_by == "created"
            # Use created_at timestamp from database
            sort_date = created_at or parse_date(pi.duration.get("start")) or datetime.now()
        
        projects_list.append({
            "project": pi,
            "sort_date": sort_date,
            "start_date": parse_date(pi.duration.get("start")),
            "end_date": parse_date(pi.duration.get("end")),
        })
    
    # Sort by date
    projects_list.sort(key=lambda x: x["sort_date"], reverse=reverse)
    
    return projects_list


def export_results(
    projects_list: List[Dict[str, Any]],
    output_dir: str = "src/analyze/projects_output"
):
    """Export chronological project list to JSON, CSV, and plain text formats."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Prepare data for export
    export_data = []
    for item in projects_list:
        project_data = item["project"]
        # Handle both ProjectInfo objects and dicts
        if isinstance(project_data, dict):
            export_data.append({
                "name": project_data.get("name", "Unknown"),
                "start_date": item["start_date"].isoformat() if item["start_date"] else None,
                "end_date": item["end_date"].isoformat() if item["end_date"] else None,
                "duration_days": project_data.get("duration", {}).get("days", 0),
                "is_collaborative": project_data.get("is_collaborative", False),
                "languages": project_data.get("languages", []),
                "frameworks": project_data.get("frameworks", []),
                "skills": project_data.get("skills", []),
                "commits": project_data.get("totals", {}).get("commits", 0),
                "files": project_data.get("totals", {}).get("files", 0),
                "lines_of_code": project_data.get("lines_of_code", 0),
                "score": project_data.get("preliminary_score", 0.0),
            })
        else:
            # ProjectInfo object
            pi = project_data
            export_data.append({
                "name": pi.name,
                "start_date": item["start_date"].isoformat() if item["start_date"] else None,
                "end_date": item["end_date"].isoformat() if item["end_date"] else None,
                "duration_days": pi.duration.get("days", 0),
                "is_collaborative": pi.is_collaborative,
                "languages": pi.languages,
                "frameworks": pi.frameworks,
                "skills": pi.skills,
                "commits": pi.totals.get("commits", 0),
                "files": pi.totals.get("files", 0),
                "lines_of_code": pi.lines_of_code,
                "score": pi.preliminary_score,
            })
    
    # JSON
    json_path = Path(output_dir) / "chronological_projects.json"
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(export_data, jf, indent=2)
    print(f"[✓] JSON exported: {json_path}")
    
    # CSV
    csv_path = Path(output_dir) / "chronological_projects.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow([
            "start_date", "end_date", "duration_days", "name", "is_collaborative",
            "languages", "frameworks", "skills", "commits", "files", "lines_of_code", "score"
        ])
        for item in export_data:
            writer.writerow([
                item["start_date"] or "",
                item["end_date"] or "",
                item["duration_days"],
                item["name"],
                item["is_collaborative"],
                ", ".join(item["languages"]),
                ", ".join(item["frameworks"]),
                ", ".join(item["skills"]),
                item["commits"],
                item["files"],
                item["lines_of_code"],
                item["score"],
            ])
    print(f"[✓] CSV exported: {csv_path}")
    
    # TXT summary
    txt_path = Path(output_dir) / "chronological_projects.txt"
    with open(txt_path, "w", encoding="utf-8") as tf:
        tf.write("=== Chronological Project List ===\n\n")
        for idx, item in enumerate(projects_list, 1):
            project_data = item["project"]
            start_str = item["start_date"].strftime('%Y-%m-%d %H:%M:%S') if item["start_date"] else "N/A"
            end_str = item["end_date"].strftime('%Y-%m-%d %H:%M:%S') if item["end_date"] else "N/A"
            
            if isinstance(project_data, dict):
                name = project_data.get("name", "Unknown")
                duration_days = project_data.get("duration", {}).get("days", 0)
                is_collab = project_data.get("is_collaborative", False)
                languages = project_data.get("languages", [])
                skills = project_data.get("skills", [])
                totals = project_data.get("totals", {})
                loc = project_data.get("lines_of_code", 0)
            else:
                name = project_data.name
                duration_days = project_data.duration.get('days', 0)
                is_collab = project_data.is_collaborative
                languages = project_data.languages
                skills = project_data.skills
                totals = project_data.totals
                loc = project_data.lines_of_code
            
            tf.write(f"{idx}. {name}\n")
            tf.write(f"   Period: {start_str} to {end_str} ({duration_days} days)\n")
            tf.write(f"   Type: {'Collaborative' if is_collab else 'Individual'}\n")
            if languages:
                tf.write(f"   Languages: {', '.join(languages)}\n")
            if skills:
                tf.write(f"   Skills: {', '.join(skills)}\n")
            tf.write(f"   Commits: {totals.get('commits', 0)}, Files: {totals.get('files', 0)}, LOC: {loc}\n\n")
    print(f"[✓] TXT exported: {txt_path}")
    
    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "txt": str(txt_path)
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate chronological timeline of projects from directory or database"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="tests/categorize/demo_projects",
        help="Directory path containing projects (default: tests/categorize/demo_projects)"
    )
    parser.add_argument(
        "--from-db",
        action="store_true",
        help="Load projects from database instead of directory"
    )
    parser.add_argument(
        "--sort-by",
        choices=["start", "created"],
        default="start",
        help="Sort by project start date or creation date (default: start)"
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Reverse order (newest first)"
    )
    parser.add_argument(
        "--output-dir",
        default="src/analyze/projects_output",
        help="Output directory for results (default: src/analyze/projects_output)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "txt", "all"],
        default="all",
        help="Output format (default: all)"
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Don't print results to stdout (only export to files)"
    )
    parser.add_argument(
        "--db-path",
        help="Override database path (only used with --from-db)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("📅 CHRONOLOGICAL PROJECT LIST")
    print("=" * 70)
    
    # Build chronological list
    if args.from_db:
        print(f"\n[1/3] Loading projects from database...")
        store = ProjectInsightsStore(db_path=args.db_path) if args.db_path else ProjectInsightsStore()
        projects_list = build_chronological_project_list(store, sort_by=args.sort_by, reverse=args.reverse)
        
        if not projects_list:
            print("❌ No projects found in database.")
            print("\nTo add projects, run:")
            print("  python3 test_repository_analysis.py --repo <path>")
            print("  or")
            print("  python3 -m src.pipeline.orchestrator <path/to/project.zip>")
            return
        
        print(f"   ✓ Loaded {len(projects_list)} project(s)")
    else:
        print(f"\n[1/3] Analyzing directory: {args.directory}")
        try:
            projects_list = build_chronological_project_list_from_directory(
                args.directory,
                sort_by=args.sort_by,
                reverse=args.reverse
            )
            
            if not projects_list:
                print(f"❌ No projects found in directory: {args.directory}")
                return
            
            print(f"   ✓ Found {len(projects_list)} project(s)")
        except Exception as e:
            print(f"❌ Error analyzing directory: {e}")
            return
    
    # Print to stdout by default
    if not args.no_print:
        print("\n" + "=" * 70)
        print("CHRONOLOGICAL PROJECT TIMELINE")
        print("=" * 70)
        
        for idx, item in enumerate(projects_list, 1):
            project_data = item["project"]
            start_str = item["start_date"].strftime('%Y-%m-%d %H:%M:%S') if item["start_date"] else "N/A"
            end_str = item["end_date"].strftime('%Y-%m-%d %H:%M:%S') if item["end_date"] else "N/A"
            duration_days = project_data.get("duration", {}).get("days", 0)
            
            print(f"\n[{idx}] {project_data.get('name', 'Unknown')}")
            print(f"  Period: {start_str} → {end_str} ({duration_days} days)")
            print(f"  Type: {'Collaborative' if project_data.get('is_collaborative') else 'Individual'}")
            
            languages = project_data.get('languages', [])
            if languages:
                print(f"  Languages: {', '.join(languages[:5])}")
            frameworks = project_data.get('frameworks', [])
            if frameworks:
                print(f"  Frameworks: {', '.join(frameworks[:5])}")
            skills = project_data.get('skills', [])
            if skills:
                print(f"  Skills: {', '.join(skills[:5])}")
            
            totals = project_data.get('totals', {})
            print(f"  Metrics: {totals.get('commits', 0)} commits, {totals.get('files', 0)} files, {project_data.get('lines_of_code', 0)} LOC")
            score = project_data.get('preliminary_score', 0.0)
            if score > 0:
                print(f"  Score: {score:.4f}")
    
    # Prepare data for database storage (only if loading from DB)
    if args.from_db:
        chronological_data = {
            "projects": [],
            "total_projects": len(projects_list),
            "sorted_by": args.sort_by,
            "reverse": args.reverse,
            "generated_at": datetime.now().isoformat()
        }
        
        for item in projects_list:
            pi = item["project"]
            chronological_data["projects"].append({
                "id": pi.id,
                "name": pi.name,
                "start_date": item["start_date"].isoformat() if item["start_date"] else None,
                "end_date": item["end_date"].isoformat() if item["end_date"] else None,
                "duration_days": pi.duration.get("days", 0),
                "is_collaborative": pi.is_collaborative,
                "languages": pi.languages,
                "frameworks": pi.frameworks,
                "skills": pi.skills,
                "commits": pi.totals.get("commits", 0),
                "files": pi.totals.get("files", 0),
                "lines_of_code": pi.lines_of_code,
                "score": pi.preliminary_score,
            })
        
        # Save to database
        print(f"\n[2/3] Saving to database...")
        try:
            # Get all unique zip hashes from projects
            all_projects = store.list_all_projects()
            zip_hashes = set(p.get('zip_hash') for p in all_projects if p.get('zip_hash'))
            
            saved_count = 0
            import sqlite3
            from insights.storage import DEFAULT_DB_PATH
            
            # Connect to database directly to update global_insights
            db_path = args.db_path if args.db_path else DEFAULT_DB_PATH
            with sqlite3.connect(db_path) as conn:
                for zip_hash in zip_hashes:
                    try:
                        # Get all projects for this zip
                        projects_in_zip = [p for p in all_projects if p.get('zip_hash') == zip_hash]
                        
                        for proj in projects_in_zip:
                            project_id = proj['id']
                            # Load current payload
                            row = conn.execute(
                                "SELECT insights_encrypted FROM project WHERE id = ?;",
                                (project_id,)
                            ).fetchone()
                            
                            if row:
                                # Decrypt, update, and re-encrypt
                                payload = store.serializer.decrypt(row[0])
                                if payload:
                                    # Update global_insights
                                    if 'global_insights' not in payload:
                                        payload['global_insights'] = {}
                                    payload['global_insights']['chronological_projects'] = chronological_data
                                    
                                    # Re-encrypt and save
                                    encrypted = store.serializer.encrypt(payload)
                                    conn.execute(
                                        "UPDATE project SET insights_encrypted = ?, updated_at = ? WHERE id = ?;",
                                        (encrypted, datetime.now().isoformat(), project_id)
                                    )
                                    saved_count += 1
                    except Exception as e:
                        print(f"   ⚠️  Warning: Could not save for zip {zip_hash[:20]}...: {e}")
                        continue
                
                conn.commit()
            
            if saved_count > 0:
                print(f"   ✓ Saved chronological project list to {saved_count} project record(s)")
            else:
                print(f"   ⚠️  Could not save to database")
        except Exception as e:
            print(f"   ⚠️  Warning: Database save failed: {e}")
    
    # Export results
    step_num = "3/3" if args.from_db else "2/2"
    print(f"\n[{step_num}] Exporting results...")
    if args.format in ["all", "json", "csv", "txt"]:
        export_paths = export_results(projects_list, output_dir=args.output_dir)
        
        if args.format != "all":
            format_map = {"json": "json", "csv": "csv", "txt": "txt"}
            print(f"\n[✓] Exported {args.format.upper()}: {export_paths[format_map[args.format]]}")
        else:
            print(f"\n[✓] Exported all formats to: {args.output_dir}")
    
    print("\n" + "=" * 70)
    print(f"Total Projects: {len(projects_list)}")
    print(f"Sorted by: {args.sort_by} date ({'newest first' if args.reverse else 'oldest first'})")
    print("=" * 70)


if __name__ == "__main__":
    main()

