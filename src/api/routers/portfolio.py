"""
Portfolio API router.

Provides GET /portfolio/{project_id} with optional ?template=industry or ?template=academic
to tailor the response for professional (impact, deliverables) vs academic (rigor, artifacts)
contexts. Also supports edit, generate, template listing, and site generation endpoints.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.deps import get_role_store, get_store
from src.insights.storage import ProjectInsightsStore
from src.insights.user_role_store import ProjectRoleStore
from src.pipeline.presentation_pipeline import PresentationPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

PortfolioTemplate = Literal["industry", "academic"]

INDUSTRY_FOCUS_FIELDS = ("impact_summary", "deliverables", "team_context", "emphasis", "tagline", "project_type")
ACADEMIC_FOCUS_FIELDS = ("context_summary", "artifacts", "documentation", "test_coverage", "emphasis", "tagline", "complexity")

# Template-specific keys added to the base portfolio response when ?template= is used.
# Industry: emphasizes deliverables, impact metrics, team size.
# Academic: emphasizes documentation, test coverage, artifacts, reproducibility.

SECTION_IDS = {
    "industry": {"impact", "deliverables", "skills", "metrics"},
    "academic": {"context", "artifacts", "documentation", "technical_skills", "metrics"},
}


def _build_key_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "total_files": metrics.get("total_files", 0),
        "total_lines": metrics.get("total_lines", 0),
        "total_commits": metrics.get("total_commits", 0),
        "total_contributors": metrics.get("total_contributors", 0),
        "doc_files": metrics.get("doc_files", 0),
        "image_files": metrics.get("image_files", 0),
        "video_files": metrics.get("video_files", 0),
        "test_files": metrics.get("test_files", 0),
    }


def _industry_impact_summary(metrics: Dict[str, Any], portfolio_item: Dict[str, Any]) -> str:
    """Build impact-focused summary for industry template."""
    parts: List[str] = []
    commits = metrics.get("total_commits", 0)
    if commits > 0:
        parts.append(f"{commits} commits")
    contributors = metrics.get("total_contributors", 0)
    if contributors > 1:
        parts.append(f"{contributors}-person team")
    lines = metrics.get("total_lines", 0)
    if lines > 0:
        parts.append(f"{lines:,} LOC")
    if parts:
        return "Delivered " + ", ".join(parts) + "."
    return portfolio_item.get("description") or portfolio_item.get("summary") or "Professional project deliverable."


def _academic_context_summary(metrics: Dict[str, Any], portfolio_item: Dict[str, Any]) -> str:
    """Build research-focused summary for academic template."""
    parts: List[str] = []
    if metrics.get("doc_files", 0) > 0:
        parts.append("documented")
    if metrics.get("test_files", 0) > 0:
        parts.append("test-covered")
    if metrics.get("total_contributors", 0) > 1:
        parts.append("collaborative")
    base = portfolio_item.get("description") or portfolio_item.get("summary") or "Research/technical project."
    if parts:
        return f"{base} ({', '.join(parts)})."
    return base


def _industry_deliverables(portfolio_item: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
    """Extract deliverables for industry-facing presentation."""
    features = portfolio_item.get("key_features") or []
    deliverables: List[str] = []
    for f in features[:6]:
        if isinstance(f, str) and f.strip():
            deliverables.append(f.strip())
    langs = portfolio_item.get("languages") or metrics.get("skills") or []
    if langs and len(deliverables) < 4:
        tech = ", ".join(str(x) for x in langs[:5])
        deliverables.append(f"Tech stack: {tech}")
    return deliverables or ["See description for details."]


def _academic_artifacts(portfolio_item: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
    """Extract research artifacts for academic presentation."""
    artifacts: List[str] = []
    if metrics.get("doc_files", 0) > 0:
        artifacts.append("Documentation included")
    if metrics.get("test_files", 0) > 0:
        artifacts.append("Test suite present")
    features = portfolio_item.get("key_features") or []
    for f in features[:5]:
        if isinstance(f, str) and f.strip():
            artifacts.append(f.strip())
    frameworks = portfolio_item.get("frameworks") or []
    if frameworks:
        artifacts.append(f"Frameworks: {', '.join(str(x) for x in frameworks[:5])}")
    return artifacts or ["Technical implementation details available."]


def _apply_industry_template(
    response: Dict[str, Any],
    portfolio_item: Dict[str, Any],
    project_metrics: Dict[str, Any],
) -> None:
    """Apply industry-style formatting to the portfolio response."""
    response["template"] = "industry"
    response["impact_summary"] = _industry_impact_summary(project_metrics, portfolio_item)
    response["deliverables"] = _industry_deliverables(portfolio_item, project_metrics)
    response["emphasis"] = "impact"
    if portfolio_item.get("is_collaborative") and project_metrics.get("total_contributors", 0) > 1:
        response["team_context"] = f"{project_metrics.get('total_contributors', 0)} contributors"
    response["tagline"] = portfolio_item.get("tagline")
    response["project_type"] = portfolio_item.get("project_type")
    response["metrics_formatted"] = _format_metrics_for_industry(response.get("key_metrics") or project_metrics)


def _apply_academic_template(
    response: Dict[str, Any],
    portfolio_item: Dict[str, Any],
    project_metrics: Dict[str, Any],
) -> None:
    """Apply academic-style formatting to the portfolio response."""
    response["template"] = "academic"
    response["context_summary"] = _academic_context_summary(project_metrics, portfolio_item)
    response["artifacts"] = _academic_artifacts(portfolio_item, project_metrics)
    response["emphasis"] = "rigor"
    if project_metrics.get("doc_files", 0) > 0:
        response["documentation"] = {
            "files": project_metrics.get("doc_files", 0),
            "available": True,
        }
    if project_metrics.get("test_files", 0) > 0:
        response["test_coverage"] = {"test_files": project_metrics.get("test_files", 0)}
    response["tagline"] = portfolio_item.get("tagline")
    response["complexity"] = portfolio_item.get("complexity")
    response["metrics_formatted"] = _format_metrics_for_academic(response.get("key_metrics") or project_metrics)


def _format_metrics_for_industry(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Format key metrics with industry-friendly labels and groupings."""
    return {
        "scale": {
            "lines_of_code": metrics.get("total_lines", 0),
            "commits": metrics.get("total_commits", 0),
            "files": metrics.get("total_files", 0),
        },
        "collaboration": {
            "contributors": metrics.get("total_contributors", 0),
            "is_team_project": metrics.get("total_contributors", 0) > 1,
        },
        "quality": {
            "documentation_files": metrics.get("doc_files", 0),
            "test_files": metrics.get("test_files", 0),
        },
    }


def _format_metrics_for_academic(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Format key metrics with academic/research-friendly structure."""
    return {
        "implementation": {
            "total_lines": metrics.get("total_lines", 0),
            "total_files": metrics.get("total_files", 0),
            "languages_frameworks": True,
        },
        "reproducibility": {
            "documentation_files": metrics.get("doc_files", 0),
            "test_files": metrics.get("test_files", 0),
        },
        "contribution": {
            "commits": metrics.get("total_commits", 0),
            "contributors": metrics.get("total_contributors", 0),
        },
    }


def _build_industry_sections(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build ordered section list for industry-style rendering."""
    sections: List[Dict[str, Any]] = []
    if response.get("impact_summary"):
        sections.append({"id": "impact", "title": "Impact", "content": response["impact_summary"]})
    if response.get("deliverables"):
        sections.append({"id": "deliverables", "title": "Deliverables", "items": response["deliverables"]})
    if response.get("key_skills"):
        sections.append({"id": "skills", "title": "Key Skills", "items": response["key_skills"]})
    if response.get("key_metrics"):
        sections.append({"id": "metrics", "title": "Metrics", "data": response["key_metrics"]})
    return sections


def _build_academic_sections(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build ordered section list for academic-style rendering."""
    sections: List[Dict[str, Any]] = []
    if response.get("context_summary"):
        sections.append({"id": "context", "title": "Context", "content": response["context_summary"]})
    if response.get("artifacts"):
        sections.append({"id": "artifacts", "title": "Artifacts", "items": response["artifacts"]})
    if response.get("documentation"):
        sections.append({"id": "documentation", "title": "Documentation", "data": response["documentation"]})
    if response.get("key_skills"):
        sections.append({"id": "technical_skills", "title": "Technical Skills", "items": response["key_skills"]})
    if response.get("key_metrics"):
        sections.append({"id": "metrics", "title": "Project Metrics", "data": response["key_metrics"]})
    return sections


def _resolve_template(template: Optional[str]) -> Optional[PortfolioTemplate]:
    """
    Normalize and validate template query value. Returns 'industry' or 'academic',
    or None if invalid/absent. Used when template may come from non-Query sources.
    """
    if not template or not isinstance(template, str):
        return None
    t = template.strip().lower()
    if t in ("industry", "academic"):
        return t
    return None


def _template_adds_sections(template: Optional[PortfolioTemplate]) -> bool:
    """True if the template adds a 'sections' array to the response."""
    return template in ("industry", "academic")


def _get_template_config(template_id: PortfolioTemplate) -> Dict[str, Any]:
    """Return configuration metadata for a template."""
    configs: Dict[str, Dict[str, Any]] = {
        "industry": {
            "id": "industry",
            "name": "Industry",
            "description": "Impact-focused: deliverables, metrics, team context, professional tone.",
            "query": "?template=industry",
            "focus_fields": list(INDUSTRY_FOCUS_FIELDS),
            "example_url": "/portfolio/{project_id}?template=industry",
        },
        "academic": {
            "id": "academic",
            "name": "Academic",
            "description": "Research-focused: rigor, documentation, artifacts, methodological context.",
            "query": "?template=academic",
            "focus_fields": list(ACADEMIC_FOCUS_FIELDS),
            "example_url": "/portfolio/{project_id}?template=academic",
        },
    }
    return configs.get(template_id, {})


@router.get("/templates")
def list_templates():
    """List available portfolio templates and their descriptions."""
    return {
        "templates": [
            _get_template_config("industry"),
            _get_template_config("academic"),
        ],
        "default": "Omit ?template for standard portfolio response.",
        "usage": "GET /portfolio/{project_id}?template=industry or ?template=academic",
    }


@router.get("/templates/{template_id}")
def get_template_detail(template_id: PortfolioTemplate):
    """Get detailed configuration for a specific template (industry or academic)."""
    return _get_template_config(template_id)


def _score_project(payload: Dict[str, Any]) -> float:
    """Derive a simple ranking score from stored project metrics."""
    metrics = payload.get("project_metrics") or {}
    commits = int(metrics.get("total_commits") or 0)
    loc = int(metrics.get("total_lines") or 0)
    code_frac = float(metrics.get("code_frac") or 0.0)
    return 0.5 * commits + 0.4 * (loc ** 0.5) + 0.1 * (code_frac * 100)


def _build_evolution(git: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Extract commit-activity data that illustrates a project's evolution over time."""
    return {
        "first_commit_at": git.get("first_commit_at"),
        "last_commit_at": git.get("last_commit_at"),
        "duration_days": git.get("duration_days") or metrics.get("duration_days", 0),
        "total_commits": git.get("total_commits") or metrics.get("total_commits", 0),
        "contributors": git.get("contributors") or [],
        "activity_mix": git.get("activity_mix") or {},
    }


@router.get("/top")
def get_top_projects(
    limit: int = Query(default=3, ge=1, le=10, description="Number of top projects to return (1–10)"),
    mode: str = Query(default="private", description="'public' strips customization fields; 'private' includes them"),
    store: ProjectInsightsStore = Depends(get_store),
):
    """
    Return the top-ranked projects ordered by a composite score (commits + LOC).

    - **limit**: how many projects to return (default 3, max 10).
    - **mode=public**: read-only view — omits editable customization fields.
    - **mode=private**: full view including tagline, description, key_features, etc.

    Each entry includes an ``evolution`` block with first/last commit dates,
    duration, total commits, contributors, and activity mix — illustrating the
    process and progression of changes over the project's lifetime.
    """
    pipeline = PresentationPipeline(insights_store=store)
    all_projects = pipeline.list_available_projects()

    if not all_projects:
        raise HTTPException(status_code=404, detail="No projects found")

    scored: List[Dict[str, Any]] = []
    for item in all_projects:
        pid = item.get("project_id")
        if not isinstance(pid, int):
            continue
        payload = store.load_project_insight_by_id(pid)
        if not payload:
            continue
        scored.append({"project_id": pid, "payload": payload, "score": _score_project(payload)})

    ranked = sorted(scored, key=lambda x: x["score"], reverse=True)[:limit]

    is_public = mode.strip().lower() == "public"
    result: List[Dict[str, Any]] = []
    for rank, entry in enumerate(ranked, start=1):
        pid = entry["project_id"]
        payload = entry["payload"]
        portfolio_item = payload.get("portfolio_item") or {}
        project_metrics = payload.get("project_metrics") or {}
        git = payload.get("git_analysis") or {}

        project: Dict[str, Any] = {
            "rank": rank,
            "project_id": pid,
            "project_title": payload.get("project_name"),
            "score": round(entry["score"], 2),
            "key_skills": portfolio_item.get("skills") or project_metrics.get("skills") or [],
            "key_metrics": _build_key_metrics(project_metrics),
            "evolution": _build_evolution(git, project_metrics),
        }

        if not is_public:
            project["tagline"] = portfolio_item.get("tagline")
            project["description"] = portfolio_item.get("description")
            project["summary"] = portfolio_item.get("summary")
            project["key_features"] = portfolio_item.get("key_features") or []
            project["project_type"] = portfolio_item.get("project_type")
            project["complexity"] = portfolio_item.get("complexity")
            project["is_collaborative"] = portfolio_item.get("is_collaborative", False)
        else:
            project["summary"] = portfolio_item.get("summary") or portfolio_item.get("description")

        result.append(project)

    return {"total": len(result), "limit": limit, "mode": mode.strip().lower(), "projects": result}


def _iso_week_key(iso_date: str) -> Optional[str]:
    """Return the ISO-8601 week start (Monday) for a date string, or None if unparseable."""
    raw = iso_date.split("T")[0] if "T" in iso_date else iso_date
    try:
        d = datetime.date.fromisoformat(raw)
    except ValueError:
        return None
    # Monday of the ISO week
    monday = d - datetime.timedelta(days=d.weekday())
    return monday.isoformat()


def _weeks_from_range(start_iso: str, end_iso: str) -> List[str]:
    """Generate all Monday-week keys between two ISO date strings (inclusive)."""
    try:
        start = datetime.date.fromisoformat(start_iso.split("T")[0])
        end = datetime.date.fromisoformat(end_iso.split("T")[0])
    except ValueError:
        return []
    start = start - datetime.timedelta(days=start.weekday())
    weeks = []
    cur = start
    while cur <= end:
        weeks.append(cur.isoformat())
        cur += datetime.timedelta(weeks=1)
    return weeks


def _heatmap_from_timeline(timeline: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count activity events per ISO week from a chronological skills timeline."""
    counts: Dict[str, int] = {}
    for event in timeline:
        ts = event.get("timestamp", "")
        week = _iso_week_key(ts) if ts else None
        if week:
            counts[week] = counts.get(week, 0) + 1
    return counts


def _heatmap_from_range(start_iso: Optional[str], end_iso: Optional[str], total: int) -> Dict[str, int]:
    """
    Synthesize a weekly heatmap when no per-event timeline exists.
    Distributes ``total`` commits evenly across weeks in [start, end].
    """
    if not start_iso or not end_iso or total <= 0:
        return {}
    weeks = _weeks_from_range(start_iso, end_iso)
    if not weeks:
        return {}
    base, remainder = divmod(total, len(weeks))
    return {week: base + (1 if i < remainder else 0) for i, week in enumerate(weeks)}


def _merge_heatmaps(maps: List[Dict[str, int]]) -> Dict[str, int]:
    """Sum multiple {week: count} maps into one."""
    merged: Dict[str, int] = {}
    for m in maps:
        for week, count in m.items():
            merged[week] = merged.get(week, 0) + count
    return merged


@router.get("/heatmap")
def get_activity_heatmap(
    store: ProjectInsightsStore = Depends(get_store),
):
    """
    Return a weekly commit-activity heatmap across all projects.

    Each key in ``weeks`` is an ISO-8601 date (Monday of the week, e.g. ``"2025-09-01"``).
    The value is the number of activity events (commits / file changes) recorded that week.

    - If chronological-skills timeline data exists for a project, actual per-file event
      timestamps are used (most accurate).
    - Otherwise, total commits are distributed evenly across the project's active date range.

    The response also includes ``total_weeks`` (number of active weeks), ``total_activity``
    (sum of all counts), and the ``date_range`` covered.
    """
    pipeline = PresentationPipeline(insights_store=store)
    all_projects = pipeline.list_available_projects()

    if not all_projects:
        raise HTTPException(status_code=404, detail="No projects found")

    per_project_maps: List[Dict[str, int]] = []
    for item in all_projects:
        pid = item.get("project_id")
        if not isinstance(pid, int):
            continue
        payload = store.load_project_insight_by_id(pid)
        if not payload:
            continue
        # Prefer timeline events for accuracy
        timeline = (
            (payload.get("global_insights") or {})
            .get("chronological_skills", {})
            .get("timeline") or []
        )
        if timeline:
            per_project_maps.append(_heatmap_from_timeline(timeline))
        else:
            metrics = payload.get("project_metrics") or {}
            per_project_maps.append(
                _heatmap_from_range(
                    metrics.get("duration_start"),
                    metrics.get("duration_end"),
                    int(metrics.get("total_commits") or 0),
                )
            )

    merged = _merge_heatmaps(per_project_maps)

    if not merged:
        return {"weeks": {}, "total_weeks": 0, "total_activity": 0, "date_range": None}

    sorted_weeks = sorted(merged)
    return {
        "weeks": {w: merged[w] for w in sorted_weeks},
        "total_weeks": len(sorted_weeks),
        "total_activity": sum(merged.values()),
        "date_range": {"start": sorted_weeks[0], "end": sorted_weeks[-1]},
    }


@router.get("/{project_id}")
def get_portfolio_showcase(
    project_id: int,
    template: Optional[PortfolioTemplate] = Query(
        default=None,
        description="Presentation style: 'industry' (impact/deliverables) or 'academic' (rigor/artifacts)",
    ),
    store: ProjectInsightsStore = Depends(get_store),
    role_store: ProjectRoleStore = Depends(get_role_store),
):
    """
    Get portfolio showcase for a project. Use ?template=industry or ?template=academic
    to tailor the response for professional vs research contexts.
    """
    payload = store.load_project_insight_by_id(project_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Project not found")

    metadata = PresentationPipeline(insights_store=store)._get_project_metadata(project_id)
    user_role: Optional[str] = None
    if metadata:
        user_role = role_store.get_user_role(metadata["zip_hash"], metadata["project_name"])

    project_name = payload.get("project_name")
    portfolio_item = payload.get("portfolio_item") or {}
    project_metrics = payload.get("project_metrics") or {}
    key_skills = portfolio_item.get("skills") or project_metrics.get("skills") or []

    response: Dict[str, Any] = {
        "project_id": project_id,
        "project_title": project_name,
        "user_role": user_role,
        "description": portfolio_item.get("description"),
        "summary": portfolio_item.get("summary") or portfolio_item.get("description"),
        "key_skills": key_skills,
        "key_metrics": _build_key_metrics(project_metrics),
    }

    thumbnail = store.get_project_thumbnail(project_id)
    if thumbnail and thumbnail.get("image_path"):
        thumb_path = Path(thumbnail["image_path"])
        if thumb_path.exists():
            response["thumbnail_path"] = str(thumb_path)
            response["thumbnail_url"] = f"/projects/{project_id}/thumbnail/content"

    success_metrics = payload.get("success_metrics")
    if success_metrics and "error" not in success_metrics:
        response["success_metrics"] = success_metrics

    if template == "industry":
        _apply_industry_template(response, portfolio_item, project_metrics)
        response["sections"] = _build_industry_sections(response)
    elif template == "academic":
        _apply_academic_template(response, portfolio_item, project_metrics)
        response["sections"] = _build_academic_sections(response)

    return response


class PortfolioEditPayload(BaseModel):
    tagline: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    complexity: Optional[str] = None
    is_collaborative: Optional[bool] = None
    summary: Optional[str] = None
    key_features: Optional[List[str]] = Field(default=None)


@router.post("/{project_id}/edit")
def edit_portfolio(
    project_id: int,
    payload: PortfolioEditPayload,
    store: ProjectInsightsStore = Depends(get_store),
):
    fields: Dict[str, Any] = {}
    for k in ("tagline", "description", "project_type", "complexity", "is_collaborative", "summary", "key_features"):
        v = getattr(payload, k)
        if v is not None:
            fields[k] = v
    changed = store.update_portfolio_insights_fields(project_id, fields)
    if not changed:
        raise HTTPException(status_code=404, detail="Project not found or no changes")
    updated = store.load_project_insight_by_id(project_id)
    return {"status": "ok", "project_id": project_id, "portfolio_item": updated.get("portfolio_item")}


@router.post("/generate")
def generate_portfolio(project_id: int, store: ProjectInsightsStore = Depends(get_store)):
    from src.project.presentation import generate_items_from_project_id

    result = generate_items_from_project_id(project_id, store=store, regenerate=True)
    portfolio = result.get("portfolio_item") or {}
    persist_fields = {
        k: portfolio.get(k)
        for k in ("tagline", "description", "project_type", "complexity", "is_collaborative", "summary", "key_features")
        if k in portfolio
    }
    if persist_fields:
        store.update_portfolio_insights_fields(project_id, persist_fields)
    return {"project_id": project_id, "portfolio_item": portfolio}


# ---------------------------------------------------------------------------
# Portfolio site generation
# ---------------------------------------------------------------------------

_portfolio_dev_pid: Optional[int] = None

PORTFOLIO_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "portfolio-template"


class PortfolioSiteRequest(BaseModel):
    name: str
    title: str = "Full-Stack Developer"
    bio: str = ""
    email: str = ""
    location: str = ""
    github_url: str = ""
    linkedin_url: str = ""
    years_experience: str = ""
    projects_completed: str = ""
    open_source_contributions: str = ""
    project_ids: List[int] = Field(..., min_length=2, max_length=4)


def _build_heatmap_data(store: ProjectInsightsStore) -> Optional[Dict[str, Any]]:
    """Aggregate the activity heatmap across all projects in the store."""
    pipeline = PresentationPipeline(insights_store=store)
    all_projects = pipeline.list_available_projects()
    if not all_projects:
        return None

    per_project_maps: List[Dict[str, int]] = []
    for item in all_projects:
        pid = item.get("project_id")
        if not isinstance(pid, int):
            continue
        payload = store.load_project_insight_by_id(pid)
        if not payload:
            continue
        timeline = (payload.get("git_analysis") or {}).get("timeline") or []
        if timeline:
            per_project_maps.append(_heatmap_from_timeline(timeline))
        else:
            metrics = payload.get("project_metrics") or {}
            per_project_maps.append(
                _heatmap_from_range(
                    metrics.get("duration_start"),
                    metrics.get("duration_end"),
                    int(metrics.get("total_commits") or 0),
                )
            )

    merged = _merge_heatmaps(per_project_maps)
    if not merged:
        return None

    sorted_weeks = sorted(merged.keys())
    return {
        "weeks": {k: merged[k] for k in sorted_weeks},
        "total_weeks": len(sorted_weeks),
        "total_activity": sum(merged.values()),
        "date_range": {"start": sorted_weeks[0], "end": sorted_weeks[-1]},
    }


def _build_showcase_data(store: ProjectInsightsStore, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
    """Return the top-ranked projects as showcase entries."""
    pipeline = PresentationPipeline(insights_store=store)
    all_projects = pipeline.list_available_projects()
    if not all_projects:
        return None

    scored: List[Dict[str, Any]] = []
    for item in all_projects:
        pid = item.get("project_id")
        if not isinstance(pid, int):
            continue
        payload = store.load_project_insight_by_id(pid)
        if not payload:
            continue
        scored.append({"project_id": pid, "payload": payload, "score": _score_project(payload)})

    ranked = sorted(scored, key=lambda x: x["score"], reverse=True)[:limit]
    result: List[Dict[str, Any]] = []
    for rank, entry in enumerate(ranked, start=1):
        pid = entry["project_id"]
        payload = entry["payload"]
        portfolio_item = payload.get("portfolio_item") or {}
        project_metrics = payload.get("project_metrics") or {}
        git = payload.get("git_analysis") or {}
        result.append({
            "rank": rank,
            "project_id": pid,
            "project_title": payload.get("project_name"),
            "score": round(entry["score"], 2),
            "summary": portfolio_item.get("summary") or portfolio_item.get("description"),
            "key_skills": portfolio_item.get("skills") or project_metrics.get("skills") or [],
            "key_metrics": _build_key_metrics(project_metrics),
            "evolution": _build_evolution(git, project_metrics),
        })
    return result or None


def _build_portfolio_ts(profile: Dict[str, Any]) -> str:
    """Render a syntactically valid TypeScript config from the profile dict."""

    def _js(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    socials = profile.get("socials") or []
    about = profile.get("about") or {}
    skills = profile.get("skills") or []
    projects = profile.get("projects") or []
    heatmap: Optional[Dict[str, Any]] = profile.get("heatmap")
    showcase: Optional[List[Dict[str, Any]]] = profile.get("showcase")

    socials_str = ",\n    ".join(
        f'{{ platform: {_js(s["platform"])}, url: {_js(s["url"])}, icon: {_js(s["icon"])} }}'
        for s in socials
    )

    highlights_str = ",\n      ".join(
        f'{{ label: {_js(h["label"])}, value: {_js(h["value"])} }}'
        for h in (about.get("highlights") or [])
    )

    desc_str = ",\n      ".join(_js(d) for d in (about.get("description") or []))

    skill_cats = []
    for cat in skills:
        items = ", ".join(_js(s) for s in cat["skills"])
        skill_cats.append(
            f'    {{\n      name: {_js(cat["name"])},\n      skills: [{items}],\n    }}'
        )
    skills_str = ",\n".join(skill_cats)

    proj_entries = []
    for p in projects:
        tags = ", ".join(_js(t) for t in p.get("tags", []))
        image_val = p.get("image") or "/placeholder-project.jpg"
        entry = f'    {{\n      title: {_js(p["title"])},\n      description: {_js(p.get("description", ""))},\n      image: {_js(image_val)},\n      tags: [{tags}],'
        if p.get("sourceUrl"):
            entry += f'\n      sourceUrl: {_js(p["sourceUrl"])},'
        if p.get("liveUrl"):
            entry += f'\n      liveUrl: {_js(p["liveUrl"])},'
        if p.get("featured"):
            entry += "\n      featured: true,"
        entry += "\n    }"
        proj_entries.append(entry)
    projects_str = ",\n".join(proj_entries)

    # Optional heatmap block
    heatmap_str = ""
    if heatmap:
        weeks_entries = ", ".join(
            f'{_js(k)}: {v}' for k, v in sorted(heatmap.get("weeks", {}).items())
        )
        dr = heatmap.get("date_range") or {}
        heatmap_str = (
            f'\n  heatmap: {{\n'
            f'    weeks: {{ {weeks_entries} }},\n'
            f'    total_weeks: {heatmap.get("total_weeks", 0)},\n'
            f'    total_activity: {heatmap.get("total_activity", 0)},\n'
            f'    date_range: {{ start: {_js(dr.get("start", ""))}, end: {_js(dr.get("end", ""))} }},\n'
            f'  }},'
        )

    # Optional showcase block
    showcase_str = ""
    if showcase:
        entries = []
        for p in showcase:
            evo = p.get("evolution") or {}
            km = p.get("key_metrics") or {}
            contribs = ", ".join(_js(c) for c in (evo.get("contributors") or []))
            mix_entries = ", ".join(
                f'{_js(k)}: {v}' for k, v in (evo.get("activity_mix") or {}).items()
            )
            skills_list = ", ".join(_js(s) for s in (p.get("key_skills") or []))
            entries.append(
                f'    {{\n'
                f'      rank: {p.get("rank", 0)},\n'
                f'      project_id: {p.get("project_id", 0)},\n'
                f'      project_title: {_js(p.get("project_title", ""))},\n'
                f'      score: {p.get("score", 0)},\n'
                f'      summary: {_js(p.get("summary") or "")},\n'
                f'      key_skills: [{skills_list}],\n'
                f'      key_metrics: {{\n'
                f'        total_files: {km.get("total_files", 0)},\n'
                f'        total_lines: {km.get("total_lines", 0)},\n'
                f'        total_commits: {km.get("total_commits", 0)},\n'
                f'        total_contributors: {km.get("total_contributors", 0)},\n'
                f'        doc_files: {km.get("doc_files", 0)},\n'
                f'        image_files: {km.get("image_files", 0)},\n'
                f'        video_files: {km.get("video_files", 0)},\n'
                f'        test_files: {km.get("test_files", 0)},\n'
                f'      }},\n'
                f'      evolution: {{\n'
                f'        first_commit_at: {_js(evo.get("first_commit_at"))},\n'
                f'        last_commit_at: {_js(evo.get("last_commit_at"))},\n'
                f'        duration_days: {evo.get("duration_days", 0)},\n'
                f'        total_commits: {evo.get("total_commits", 0)},\n'
                f'        contributors: [{contribs}],\n'
                f'        activity_mix: {{ {mix_entries} }},\n'
                f'      }},\n'
                f'    }}'
            )
        showcase_str = f'\n  showcase: [\n' + ",\n".join(entries) + f'\n  ],'

    return f'''import type {{ DeveloperProfile }} from "@/types/portfolio";

export const portfolio: DeveloperProfile = {{
  name: {_js(profile.get("name", ""))},
  title: {_js(profile.get("title", ""))},
  bio: {_js(profile.get("bio", ""))},
  avatarUrl: "/avatar-placeholder.jpg",
  resumeUrl: "/resume.pdf",
  email: {_js(profile.get("email", ""))},
  location: {_js(profile.get("location", ""))},

  socials: [
    {socials_str}
  ],

  about: {{
    description: [
      {desc_str}
    ],
    highlights: [
      {highlights_str}
    ],
  }},

  skills: [
{skills_str}
  ],

  projects: [
{projects_str}
  ],

  experience: [],{heatmap_str}{showcase_str}
}};
'''


def _is_running_in_docker() -> bool:
    """Detect if the process is running inside a Docker container."""
    return os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER") == "1"


def _find_npm() -> Optional[str]:
    """Return the path to npm if available, or None."""
    return shutil.which("npm")


def _ensure_dev_server() -> bool:
    """Start the Next.js dev server if it is not already running.

    Returns True if the server was started or is already running,
    False if npm is unavailable (e.g. inside Docker).
    """
    global _portfolio_dev_pid

    if _portfolio_dev_pid is not None:
        try:
            os.kill(_portfolio_dev_pid, 0)
            return True
        except OSError:
            _portfolio_dev_pid = None

    if _is_running_in_docker():
        logger.info("Running inside Docker — skipping portfolio dev server (run 'npm run dev' in portfolio-template/ on the host)")
        return False

    npm_path = _find_npm()
    if not npm_path:
        logger.warning("npm not found — cannot start portfolio dev server")
        return False

    proc = subprocess.Popen(
        [npm_path, "run", "dev"],
        cwd=str(PORTFOLIO_TEMPLATE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    _portfolio_dev_pid = proc.pid
    logger.info("Started portfolio dev server (pid=%s)", proc.pid)
    return True


@router.post("/generate-site")
def generate_portfolio_site(
    req: PortfolioSiteRequest,
    store: ProjectInsightsStore = Depends(get_store),
):
    """
    Generate a portfolio website from user profile info and selected projects.

    Writes the portfolio config, starts the Next.js dev server, and returns
    the URL where the user can view their portfolio.  The Resume button on the
    generated site serves ``portfolio-template/public/resume.pdf``, which is
    written by ``POST /resume/pdf`` whenever the user generates a resume in the
    frontend — so generate your resume first and the button will work.
    """
    socials: List[Dict[str, str]] = []
    if req.github_url:
        socials.append({"platform": "GitHub", "url": req.github_url, "icon": "github"})
    if req.linkedin_url:
        socials.append({"platform": "LinkedIn", "url": req.linkedin_url, "icon": "linkedin"})

    highlights: List[Dict[str, str]] = []
    if req.years_experience:
        highlights.append({"label": "Years Experience", "value": req.years_experience})
    if req.projects_completed:
        highlights.append({"label": "Projects Completed", "value": req.projects_completed})
    if req.open_source_contributions:
        highlights.append({"label": "Open Source Contributions", "value": req.open_source_contributions})

    all_skills: Dict[str, set] = {}
    ts_projects: List[Dict[str, Any]] = []

    for i, pid in enumerate(req.project_ids):
        payload = store.load_project_insight_by_id(pid)
        if payload is None:
            raise HTTPException(status_code=404, detail=f"Project {pid} not found")

        portfolio_item = payload.get("portfolio_item") or {}
        project_metrics = payload.get("project_metrics") or {}
        project_name = payload.get("project_name") or f"Project {pid}"

        skills_list = (
            portfolio_item.get("skills")
            or project_metrics.get("skills")
            or []
        )
        languages = portfolio_item.get("languages") or project_metrics.get("languages") or []
        frameworks = portfolio_item.get("frameworks") or project_metrics.get("frameworks") or []

        for lang in languages:
            all_skills.setdefault("Languages", set()).add(str(lang))
        for fw in frameworks:
            all_skills.setdefault("Frameworks", set()).add(str(fw))
        for sk in skills_list:
            all_skills.setdefault("Tools & Skills", set()).add(str(sk))

        tags = list(dict.fromkeys(
            [str(s) for s in languages[:3]] + [str(s) for s in frameworks[:3]] + [str(s) for s in skills_list[:3]]
        ))

        thumbnail = store.get_project_thumbnail(pid)
        image_url = "/placeholder-project.jpg"
        if thumbnail and thumbnail.get("image_path"):
            thumb_path = Path(thumbnail["image_path"])
            if thumb_path.exists():
                image_url = f"http://localhost:8000/projects/{pid}/thumbnail/content"

        ts_projects.append({
            "title": project_name,
            "description": portfolio_item.get("summary") or portfolio_item.get("description") or "",
            "image": image_url,
            "tags": tags[:6],
            "featured": i < 2,
        })

    skill_categories = [
        {"name": cat, "skills": sorted(items)}
        for cat, items in all_skills.items()
        if items
    ]

    # --- Heatmap ---------------------------------------------------------------
    heatmap_data: Optional[Dict[str, Any]] = None
    try:
        heatmap_data = _build_heatmap_data(store)
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not build heatmap data: %s", exc)

    # --- Top-3 showcase -------------------------------------------------------
    showcase_data: Optional[List[Dict[str, Any]]] = None
    try:
        showcase_data = _build_showcase_data(store, limit=3)
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not build showcase data: %s", exc)

    profile: Dict[str, Any] = {
        "name": req.name,
        "title": req.title,
        "bio": req.bio,
        "email": req.email,
        "location": req.location,
        "socials": socials,
        "about": {
            "description": [req.bio] if req.bio else [],
            "highlights": highlights,
        },
        "skills": skill_categories,
        "projects": ts_projects,
    }
    if heatmap_data:
        profile["heatmap"] = heatmap_data
    if showcase_data:
        profile["showcase"] = showcase_data

    config_path = PORTFOLIO_TEMPLATE_DIR / "src" / "config" / "portfolio.ts"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(_build_portfolio_ts(profile), encoding="utf-8")
    logger.info("Wrote portfolio config to %s", config_path)

    server_running = _ensure_dev_server()

    return {
        "status": "ok",
        "url": "http://localhost:3000",
        "server_started": server_running,
        "message": (
            "Portfolio generated. Visit http://localhost:3000 to view it."
            if server_running
            else "Portfolio config written. Run 'cd portfolio-template && npm run dev' on the host to view it at http://localhost:3000."
        ),
    }
