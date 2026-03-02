"""
Top projects ranking and summary generation.
Local-only utilities that operate on ProjectInfo objects produced by src.project.aggregator.
"""
from __future__ import annotations

import csv
import io
from dataclasses import asdict
from typing import Callable, Iterable, List, Literal, Tuple

from .aggregator import ProjectInfo, compute_rank_inputs, compute_preliminary_score


RankingCriteria = Literal[
    "score",      # use preliminary_score
    "recency",    # newer (smaller recency_days) ranks higher
    "commits",    # more total commits ranks higher
    "loc",        # more lines_of_code ranks higher
    "impact",     # weighted combo of commits, loc, code_frac
    "user_contrib", # user contribution share ranks higher
]


def _get_user_contrib_score(pi: ProjectInfo, user_email: str = None) -> float:
    """Calculate user contribution score based on email or name matching."""
    if not user_email or not pi.authors:
        return 0.0
    
    total_commits = sum(a.get("commits", 0) for a in pi.authors)
    if total_commits <= 0:
        return 0.0
    
    # Find user by email (exact match) or name (partial match)
    user_commits = 0
    for author in pi.authors:
        author_email = author.get("email", "").lower()
        author_name = author.get("name", "").lower()
        
        if (user_email.lower() == author_email or 
            user_email.lower() in author_name or
            any(part in author_name for part in user_email.lower().split('@')[0].split('.'))):
            user_commits += author.get("commits", 0)
    
    return user_commits / total_commits if total_commits > 0 else 0.0


def _get_recency_days(pi: ProjectInfo) -> int:
    return int(pi.rank_inputs.get("recency_days", 0))


def _ensure_rank(pi: ProjectInfo) -> ProjectInfo:
   
    if not pi.rank_inputs:
        pi.rank_inputs = compute_rank_inputs(pi)
    if not pi.preliminary_score:
        pi.preliminary_score = compute_preliminary_score(pi.rank_inputs)
    return pi


def _criteria_key(criteria: RankingCriteria, user_email: str = None) -> Callable[[ProjectInfo], Tuple]:

    def score_key(pi: ProjectInfo):
        pi = _ensure_rank(pi)
        return (pi.preliminary_score, pi.totals.get("commits", 0), pi.lines_of_code)

    def recency_key(pi: ProjectInfo):
        pi = _ensure_rank(pi)
        return (_get_recency_days(pi), -pi.totals.get("commits", 0), -pi.lines_of_code)

    def commits_key(pi: ProjectInfo):
        pi = _ensure_rank(pi)
        return (pi.totals.get("commits", 0), pi.preliminary_score)

    def loc_key(pi: ProjectInfo):
        pi = _ensure_rank(pi)
        return (pi.lines_of_code, pi.preliminary_score)

    def impact_key(pi: ProjectInfo):
        pi = _ensure_rank(pi)
        commits = pi.totals.get("commits", 0)
        loc = max(0, pi.lines_of_code)
        code_frac = float(pi.rank_inputs.get("code_frac", 0.0))
        composite = 0.5 * commits + 0.4 * (loc ** 0.5) + 0.1 * (code_frac * 100)
        return (round(composite, 4), pi.preliminary_score)

    def user_contrib_key(pi: ProjectInfo):
        pi = _ensure_rank(pi)
        user_score = _get_user_contrib_score(pi, user_email)
        # Also consider total commits as secondary factor
        total_commits = pi.totals.get("commits", 0)
        return (user_score, total_commits, pi.preliminary_score)

    mapping = {
        "score": score_key,
        "recency": recency_key,
        "commits": commits_key,
        "loc": loc_key,
        "impact": impact_key,
        "user_contrib": user_contrib_key,
    }
    return mapping[criteria]


def rank_projects(
    projects: Iterable[ProjectInfo],
    n: int = 5,
    criteria: RankingCriteria = "score",
    user_email: str = None,
) -> List[ProjectInfo]:
    items = [
        _ensure_rank(p)
        for p in projects
        if isinstance(p, ProjectInfo)
    ]
    if not items:
        return []

    reverse = True if criteria != "recency" else False
    key_fn = _criteria_key(criteria, user_email)
 
    ranked = sorted(items, key=key_fn, reverse=reverse)
    # Limit to 3-5 as acceptance criteria
    n = max(3, min(5, int(n)))
    return ranked[:n]


def _contribution_summary(pi: ProjectInfo) -> Tuple[str, float]:
    authors = pi.authors or []
    if not authors:
      
        return ("Individual contributor", 1.0 if not pi.is_collaborative else 0.0)
    # compute top author share by commits if available
    total_commits = sum(a.get("commits", 0) for a in authors) or 0
    if total_commits <= 0:
        
        share = 1.0 / max(1, len(authors))
        name = authors[0].get("name") or "Primary contributor"
        return (name, share)
    top = max(authors, key=lambda a: a.get("commits", 0))
    top_name = top.get("name") or "Top contributor"
    top_share = top.get("commits", 0) / total_commits
    return (top_name, top_share)


def generate_summary(
    pi: ProjectInfo,
    max_length: int = 220,
) -> str:
    pi = _ensure_rank(pi)
    name = pi.name
    score = pi.preliminary_score
    commits = pi.totals.get("commits", 0)
    loc = pi.lines_of_code
    recency = pi.rank_inputs.get("recency_days", 0)
    langs = ", ".join(pi.languages[:3]) if pi.languages else "N/A"
    duration_days = pi.duration.get("days", 0)

    contrib_name, contrib_share = _contribution_summary(pi)
    impact_bits = []
    if commits:
        impact_bits.append(f"{commits} commits")
    if loc:
        impact_bits.append(f"{loc} LOC")
    if duration_days:
        impact_bits.append(f"{duration_days} days")

    impact = ", ".join(impact_bits) if impact_bits else "No metrics"
    share_pct = int(round(contrib_share * 100))
    collab = "Collaborative" if pi.is_collaborative else "Solo"

    text = (
        f"{name} | {collab} | score {score}. "
        f"Top contributor: {contrib_name} ({share_pct}%). "
        f"Impact: {impact}. Langs: {langs}. Recency: {recency} days."
    )
    if len(text) <= max_length:
        return text

    parts = text.split(". ")
    out = []
    for p in parts:
        candidate = (". ".join(out + [p])).strip()
        if len(candidate) + 1 <= max_length:  
            out.append(p)
        else:
            break
    res = (". ".join(out)).rstrip()
    if not res.endswith("."):
        res += "."
    return res


def generate_summaries(
    projects: Iterable[ProjectInfo],
    n: int = 5,
    criteria: RankingCriteria = "score",
    max_length: int = 220,
    user_email: str = None,
) -> List[dict]:
    ranked = rank_projects(projects, n=n, criteria=criteria, user_email=user_email)
    output = []
    for rank, pi in enumerate(ranked, start=1):
        summary = generate_summary(pi, max_length=max_length)
        # Add user contribution info if user_email provided
        user_contrib_score = None
        if user_email:
            user_contrib_score = _get_user_contrib_score(pi, user_email)
        
        output.append(
            {
                "rank": rank,
                "id": pi.id,
                "name": pi.name,
                "score": pi.preliminary_score,
                "criteria": criteria,
                "summary": summary,
                "user_contrib_score": user_contrib_score,
                "metrics": {
                    "commits": pi.totals.get("commits", 0),
                    "loc": pi.lines_of_code,
                    "recency_days": pi.rank_inputs.get("recency_days", 0),
                    "languages": pi.languages,
                    "duration_days": pi.duration.get("days", 0),
                },
            }
        )
    return output


def to_format(
    summaries: List[dict],
    fmt: Literal["json", "csv", "text"] = "json",
) -> str:
    fmt = fmt.lower()
    if fmt == "json":

        import json
        return json.dumps(summaries, ensure_ascii=False, indent=2)

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "rank",
            "id",
            "name",
            "score",
            "criteria",
            "user_contrib_score",
            "commits",
            "loc",
            "recency_days",
            "duration_days",
            "languages",
            "summary",
        ])
        for s in summaries:
            m = s.get("metrics", {})
            writer.writerow([
                s.get("rank"),
                s.get("id"),
                s.get("name"),
                s.get("score"),
                s.get("criteria"),
                s.get("user_contrib_score", ""),
                m.get("commits", 0),
                m.get("loc", 0),
                m.get("recency_days", 0),
                m.get("duration_days", 0),
                ";".join(m.get("languages", [])[:5]),
                s.get("summary", ""),
            ])
        return buf.getvalue()

    if fmt == "text":
        lines = []
        for s in summaries:
            m = s.get("metrics", {})
            line = (
                f"#{s.get('rank')}: {s.get('name')} (score {s.get('score')}) - "
                f"commits {m.get('commits', 0)}, loc {m.get('loc', 0)}, "
                f"recency {m.get('recency_days', 0)}d\n    {s.get('summary', '')}"
            )
            lines.append(line)
        return "\n".join(lines)

    raise ValueError("Unsupported format; use 'json', 'csv', or 'text'")
