"""
Portfolio API router.

Provides GET /portfolio/{project_id} with optional ?template=industry or ?template=academic
to tailor the response for professional (impact, deliverables) vs academic (rigor, artifacts)
contexts. Also supports edit, generate, and template listing endpoints.
"""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.deps import get_role_store, get_store
from src.insights.storage import ProjectInsightsStore
from src.insights.user_role_store import ProjectRoleStore
from src.pipeline.presentation_pipeline import PresentationPipeline

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
