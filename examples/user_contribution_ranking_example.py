#!/usr/bin/env python3
"""
Example demonstrating user contribution ranking functionality.
"""
from src.project import from_git, merge_local_git, rank_projects, generate_summaries, to_format
from src.project.aggregator import from_local


def main():

    print("=== User Contribution Ranking Example ===\n")

    project1_git = from_git("/project1", {
        "commits": 10,
        "by_activity": {"code": 8, "test": 1, "doc": 1},
        "authors": [
            {"name": "John Doe", "email": "john@example.com", "commits": 8},
            {"name": "Jane Smith", "email": "jane@example.com", "commits": 2},
        ],
        "files_touched": 15,
        "languages": [{"ext": ".py", "count": 20}],
        "duration": {"first_commit_iso": "2024-01-01", "last_commit_iso": "2024-06-01", "days": 152},
    })
    
    project1_local = from_local("/project1", {
        "lines_of_code": 2000,
        "activity_mix": {"code": 80, "test": 10, "doc": 10},
        "skills": ["Python", "FastAPI"],
        "languages": ["Python"],
        "duration": {"start": "2024-01-01", "end": "2024-06-01", "days": 152},
        "totals": {"files": 15},
    })
    
    project1 = merge_local_git(project1_local, project1_git)
    

    project2_git = from_git("/project2", {
        "commits": 25,
        "by_activity": {"code": 20, "test": 3, "doc": 2},
        "authors": [
            {"name": "Alice Brown", "email": "alice@example.com", "commits": 20},
            {"name": "John Doe", "email": "john@example.com", "commits": 5},
        ],
        "files_touched": 30,
        "languages": [{"ext": ".js", "count": 25}, {"ext": ".ts", "count": 15}],
        "duration": {"first_commit_iso": "2024-02-01", "last_commit_iso": "2024-07-01", "days": 151},
    })
    
    project2_local = from_local("/project2", {
        "lines_of_code": 3500,
        "activity_mix": {"code": 100, "test": 15, "doc": 10},
        "skills": ["JavaScript", "TypeScript", "React"],
        "languages": ["JavaScript", "TypeScript"],
        "duration": {"start": "2024-02-01", "end": "2024-07-01", "days": 151},
        "totals": {"files": 30},
    })
    
    project2 = merge_local_git(project2_local, project2_git)
    

    project3_git = from_git("/project3", {
        "commits": 15,
        "by_activity": {"code": 12, "test": 2, "doc": 1},
        "authors": [
            {"name": "Bob Wilson", "email": "bob@example.com", "commits": 10},
            {"name": "Carol Davis", "email": "carol@example.com", "commits": 5},
        ],
        "files_touched": 20,
        "languages": [{"ext": ".py", "count": 18}, {"ext": ".java", "count": 12}],
        "duration": {"first_commit_iso": "2023-12-01", "last_commit_iso": "2024-05-01", "days": 152},
    })
    
    project3_local = from_local("/project3", {
        "lines_of_code": 2800,
        "activity_mix": {"code": 60, "test": 8, "doc": 6},
        "skills": ["Python", "Java", "Spring"],
        "languages": ["Python", "Java"],
        "duration": {"start": "2023-12-01", "end": "2024-05-01", "days": 152},
        "totals": {"files": 20},
    })
    
    project3 = merge_local_git(project3_local, project3_git)
    
    projects = [project1, project2, project3]
    user_email = "john@example.com"
    
  
    print("1. Ranking by default score (no user context):")
    summaries_score = generate_summaries(projects, criteria="score", user_email=user_email)
    for s in summaries_score:
        print(f"   #{s['rank']}: {s['name']} (score: {s['score']:.2f})")
    
    print(f"\n2. Ranking by user contribution for {user_email}:")
    summaries_user = generate_summaries(projects, criteria="user_contrib", user_email=user_email)
    for s in summaries_user:
        contrib_pct = s['user_contrib_score'] * 100 if s['user_contrib_score'] else 0
        print(f"   #{s['rank']}: {s['name']} (user contribution: {contrib_pct:.1f}%)")
    
    print(f"\n3. Ranking by total commits:")
    summaries_commits = generate_summaries(projects, criteria="commits", user_email=user_email)
    for s in summaries_commits:
        contrib_pct = s['user_contrib_score'] * 100 if s['user_contrib_score'] else 0
        commits = s['metrics']['commits']
        print(f"   #{s['rank']}: {s['name']} ({commits} commits, user contribution: {contrib_pct:.1f}%)")
    

    print(f"\n4. Detailed summary of top user-contributed project:")
    top_user_project = summaries_user[0]
    print(f"   {top_user_project['summary']}")
    
    
    print(f"\n5. Export examples:")
    
    
    json_output = to_format(summaries_user, fmt="json")
    print("   JSON output (truncated):")
    print(f"   {json_output[:200]}...")
    
    
    csv_output = to_format(summaries_user, fmt="csv")
    print("\n   CSV output:")
    lines = csv_output.strip().split('\n')[:3]  
    for line in lines:
        print(f"   {line}")
    print("   ...")
    
    print(f"\n=== Key Insights ===")
    print(f"- Project 1: John contributed 80% (8/10 commits) - RANKS #1 by user contribution")
    print(f"- Project 2: John contributed 20% (5/25 commits) - RANKS #2 by user contribution") 
    print(f"- Project 3: John contributed 0% (0/15 commits) - RANKS #3 by user contribution")
    print(f"\nNote: By total commits, the order would be Project 2 (25) > Project 3 (15) > Project 1 (10)")
    print("But user contribution ranking prioritizes projects where the user was most involved!")


if __name__ == "__main__":
    main()
