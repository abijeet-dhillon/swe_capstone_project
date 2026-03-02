import json
import csv
import io
import re
import pytest

from src.project import (
    from_local,
    from_git,
    merge_local_git,
    rank_projects,
    generate_summary,
    generate_summaries,
    to_format,
)
from src.project.top_summary import _get_user_contrib_score


def _mk_local(loc=1000, code=50, test=10, doc=5, skills=None, langs=None, duration=None, path="/x/a"):
    return from_local(
        path,
        {
            "lines_of_code": loc,
            "activity_mix": {"code": code, "test": test, "doc": doc},
            "skills": skills or ["Python"],
            "languages": langs or ["Python"],
            "duration": duration or {"start": "2024-01-01", "end": "2024-06-01", "days": 152},
            "totals": {"files": 10},
        },
    )


def _mk_git(commits=10, by_activity=None, authors=None, files=5, langs=None, duration=None, path="/x/a"):
    return from_git(
        path,
        {
            "commits": commits,
            "by_activity": by_activity or {"code": 8, "test": 1, "doc": 1},
            "authors": authors or [{"name": "A", "email": "a@x", "commits": commits}],
            "files_touched": files,
            "languages": langs or [{"ext": ".py", "count": 10}],
            "duration": duration or {"first_commit_iso": "2024-01-01", "last_commit_iso": "2024-07-01", "days": 182},
        },
    )


def test_rank_projects_limits_to_between_3_and_5():
    items = []
    for i in range(8):
        pi = _mk_local(loc=200*(i+1))
        items.append(pi)
    top = rank_projects(items, n=10, criteria="loc")
    assert 3 <= len(top) <= 5
    assert len(top) == 5

    top3 = rank_projects(items, n=2, criteria="loc")
    assert len(top3) == 3


def test_criteria_sorting_changes_order():
    a = merge_local_git(_mk_local(loc=500, path="/x/a"), _mk_git(commits=2, path="/x/a"))
    b = merge_local_git(_mk_local(loc=2000, path="/x/b"), _mk_git(commits=1, path="/x/b"))
    c = merge_local_git(_mk_local(loc=300, path="/x/c"), _mk_git(commits=50, path="/x/c"))

    by_loc = [p.id for p in rank_projects([a, b, c], n=5, criteria="loc")]
    by_commits = [p.id for p in rank_projects([a, b, c], n=5, criteria="commits")]

    assert by_loc != by_commits


def test_generate_summary_length_control():
    pi = merge_local_git(_mk_local(loc=5000, code=300, test=50, doc=50, skills=["Python","JS","SQL"], langs=["Python","JavaScript"]), _mk_git(commits=120))
    s = generate_summary(pi, max_length=120)
    assert len(s) <= 120

    
    s2 = generate_summary(pi, max_length=220)
    assert len(s2) >= len(s)


def test_generate_summaries_and_formats():
    items = [
        merge_local_git(_mk_local(loc=1000), _mk_git(commits=10)),
        merge_local_git(_mk_local(loc=2000), _mk_git(commits=5)),
        merge_local_git(_mk_local(loc=3000), _mk_git(commits=20)),
        merge_local_git(_mk_local(loc=4000), _mk_git(commits=1)),
    ]

    summaries = generate_summaries(items, n=4, criteria="impact", max_length=160)
    assert 3 <= len(summaries) <= 5
    for s in summaries:
        assert set(["rank","id","name","score","criteria","summary","metrics"]).issubset(s.keys())
        m = s["metrics"]
        assert set(["commits","loc","recency_days","languages","duration_days"]).issubset(m.keys())

    
    json_str = to_format(summaries, fmt="json")
    data = json.loads(json_str)
    assert isinstance(data, list)
    assert data[0]["criteria"] == "impact"

    
    csv_str = to_format(summaries, fmt="csv")
    reader = csv.reader(io.StringIO(csv_str))
    rows = list(reader)
    assert rows[0][:3] == ["rank","id","name"]
    assert len(rows) == len(summaries) + 1

    
    text_str = to_format(summaries, fmt="text")
    lines = [l for l in text_str.splitlines() if l.strip()]
    assert lines and lines[0].startswith("#1:")


def test_recency_criteria_orders_recent_first():
    
    old_git = _mk_git(duration={"first_commit_iso":"2022-01-01","last_commit_iso":"2023-01-01","days":365}, path="/x/old")
    old_local = _mk_local(duration={"start":"2022-01-01","end":"2023-01-01","days":365}, path="/x/old")
    old = merge_local_git(old_local, old_git)


    recent = merge_local_git(_mk_local(path="/x/recent"), _mk_git(path="/x/recent"))

    ranked = rank_projects([old, recent], n=3, criteria="recency")
    
    assert ranked[0].rank_inputs["recency_days"] <= ranked[1].rank_inputs["recency_days"]
    assert ranked[0].id == recent.id


def test_user_contrib_score_calculation():
    
    git_data = {
        "commits": 10,
        "by_activity": {"code": 8, "test": 1, "doc": 1},
        "authors": [
            {"name": "John Doe", "email": "john@example.com", "commits": 6},
            {"name": "Jane Smith", "email": "jane@example.com", "commits": 4},
        ],
        "files_touched": 5,
        "languages": [{"ext": ".py", "count": 10}],
        "duration": {"first_commit_iso": "2024-01-01", "last_commit_iso": "2024-07-01", "days": 182},
    }
    pi = from_git("/x/test", git_data)
    
   
    score = _get_user_contrib_score(pi, "john@example.com")
    assert score == 0.6  # 6/10 commits
    
    
    score = _get_user_contrib_score(pi, "unknown@example.com")
    assert score == 0.0
    
    
    score = _get_user_contrib_score(pi, "john")
    assert score == 0.6  


def test_user_contrib_ranking():

    high_contrib_git = _mk_git(
        commits=10,
        authors=[
            {"name": "John Doe", "email": "john@example.com", "commits": 8},
            {"name": "Jane Smith", "email": "jane@example.com", "commits": 2},
        ],
        path="/x/high"
    )
    high_contrib = merge_local_git(_mk_local(path="/x/high"), high_contrib_git)
    
    low_contrib_git = _mk_git(
        commits=20,
        authors=[
            {"name": "John Doe", "email": "john@example.com", "commits": 2},
            {"name": "Alice Brown", "email": "alice@example.com", "commits": 18},
        ],
        path="/x/low"
    )
    low_contrib = merge_local_git(_mk_local(path="/x/low"), low_contrib_git)
    
    
    ranked = rank_projects([high_contrib, low_contrib], n=5, criteria="user_contrib", user_email="john@example.com")
    

    assert ranked[0].id == high_contrib.id
    assert ranked[1].id == low_contrib.id


def test_generate_summaries_with_user_contrib():
    items = [
        merge_local_git(_mk_local(loc=1000, path="/x/high"), _mk_git(commits=10, authors=[
            {"name": "John Doe", "email": "john@example.com", "commits": 8},
            {"name": "Jane Smith", "email": "jane@example.com", "commits": 2},
        ], path="/x/high")),
        merge_local_git(_mk_local(loc=2000, path="/x/low"), _mk_git(commits=5, authors=[
            {"name": "John Doe", "email": "john@example.com", "commits": 1},
            {"name": "Bob Wilson", "email": "bob@example.com", "commits": 4},
        ], path="/x/low")),
        merge_local_git(_mk_local(loc=500, path="/x/medium"), _mk_git(commits=8, authors=[
            {"name": "John Doe", "email": "john@example.com", "commits": 3},
            {"name": "Alice Brown", "email": "alice@example.com", "commits": 5},
        ], path="/x/medium")),
    ]

    summaries = generate_summaries(items, n=4, criteria="user_contrib", max_length=160, user_email="john@example.com")
    assert 3 <= len(summaries) <= 5
    
    for s in summaries:
        assert "user_contrib_score" in s
        assert s["user_contrib_score"] is not None
        assert 0 <= s["user_contrib_score"] <= 1
