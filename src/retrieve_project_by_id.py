#!/usr/bin/env python3
"""
Retrieve a project by its database ID.
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from insights.storage import ProjectInsightsStore


def list_projects(store: ProjectInsightsStore):
    """List all projects with their IDs."""
    projects = store.list_all_projects()
    
    if not projects:
        print("No projects found in database.")
        return
    
    print("=" * 70)
    print("STORED PROJECTS")
    print("=" * 70)
    print(f"{'ID':<6} {'Project Name':<30} {'Zip Hash':<20} {'Created'}")
    print("-" * 70)
    
    for proj in projects:
        created = proj['created_at'][:10] if proj['created_at'] else 'N/A'
        print(f"{proj['id']:<6} {proj['project_name']:<30} {proj['zip_hash'][:18]:<20} {created}")
    
    print("=" * 70)
    print(f"Total: {len(projects)} project(s)")


def retrieve_project(store: ProjectInsightsStore, project_id: int, format_output: str = "pretty"):
    """Retrieve and display a project by ID."""
    project = store.get_project_by_id(project_id)
    
    if not project:
        print(f"❌ Project with ID {project_id} not found.")
        print("\nUse --list to see available projects.")
        return
    
    print("=" * 70)
    print(f"PROJECT ID: {project['id']}")
    print("=" * 70)
    print(f"Project Name: {project['project_name']}")
    print(f"Zip Hash: {project['zip_hash']}")
    print(f"Zip Path: {project['zip_path']}")
    print(f"Created At: {project['created_at']}")
    print()
    
    insights = project.get('insights')
    if insights:
        if format_output == "json":
            print("INSIGHTS (JSON):")
            print("=" * 70)
            print(json.dumps(insights, indent=2))
        else:
            print("INSIGHTS:")
            print("=" * 70)
            _print_insights_pretty(insights)
    else:
        print("No insights data available.")


def _print_insights_pretty(insights: dict):
    """Pretty print insights in a readable format."""
    # Project metrics
    metrics = insights.get('project_metrics', {})
    if metrics:
        print("\n📊 PROJECT METRICS:")
        print(f"  Name: {metrics.get('name', 'N/A')}")
        print(f"  Duration: {metrics.get('duration', {}).get('start', 'N/A')} to {metrics.get('duration', {}).get('end', 'N/A')}")
        print(f"  Collaborative: {metrics.get('is_collaborative', False)}")
        print(f"  Languages: {', '.join(metrics.get('languages', []))}")
        print(f"  Frameworks: {', '.join(metrics.get('frameworks', []))}")
        print(f"  Total Commits: {metrics.get('totals', {}).get('commits', 0)}")
        print(f"  Lines of Code: {metrics.get('lines_of_code', 0)}")
    
    # Portfolio item
    portfolio = insights.get('portfolio_item')
    if portfolio:
        print("\n📝 PORTFOLIO ITEM:")
        print(f"  Title: {portfolio.get('title', 'N/A')}")
        print(f"  Description: {portfolio.get('description', 'N/A')[:100]}...")
    
    # Resume item
    resume = insights.get('resume_item')
    if resume:
        print("\n📄 RESUME ITEM:")
        bullets = resume.get('bullets', [])
        for i, bullet in enumerate(bullets[:5], 1):
            print(f"  {i}. {bullet}")
        if len(bullets) > 5:
            print(f"  ... and {len(bullets) - 5} more")


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve projects by database ID from insights storage."
    )
    parser.add_argument(
        "--id",
        type=int,
        help="Project ID to retrieve"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available projects with their IDs"
    )
    parser.add_argument(
        "--format",
        choices=["pretty", "json"],
        default="pretty",
        help="Output format (default: pretty)"
    )
    parser.add_argument(
        "--db-path",
        help="Override database path"
    )
    
    args = parser.parse_args()
    
    if not args.list and args.id is None:
        parser.error("Either --id or --list must be specified")
    
    store = ProjectInsightsStore(db_path=args.db_path) if args.db_path else ProjectInsightsStore()
    
    if args.list:
        list_projects(store)
    else:
        retrieve_project(store, args.id, args.format)


if __name__ == "__main__":
    main()

