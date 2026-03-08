"""
Portfolio API router.

Provides GET /portfolio/{project_id} with optional ?template=industry or ?template=academic
to tailor the response for professional (impact, deliverables) vs academic (rigor, artifacts)
contexts. Also supports edit, generate, and template listing endpoints.
"""
from __future__ import annotations

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

    # Load payloads and score each project
    scored: List[Dict[str, Any]] = []
    for item in all_projects:
        pid = item.get("project_id")
        if not isinstance(pid, int):
            continue
        payload = store.load_project_insight_by_id(pid)
        if not payload:
            continue
        scored.append({"project_id": pid, "payload": payload, "score": _score_project(payload)})

    # Rank descending by score; limit to requested N
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
            # Private mode: include all customization fields
            project["tagline"] = portfolio_item.get("tagline")
            project["description"] = portfolio_item.get("description")
            project["summary"] = portfolio_item.get("summary")
            project["key_features"] = portfolio_item.get("key_features") or []
            project["project_type"] = portfolio_item.get("project_type")
            project["complexity"] = portfolio_item.get("complexity")
            project["is_collaborative"] = portfolio_item.get("is_collaborative", False)
        else:
            # Public mode: only the summary (read-only description)
            project["summary"] = portfolio_item.get("summary") or portfolio_item.get("description")

        result.append(project)

    return {"total": len(result), "limit": limit, "mode": mode.strip().lower(), "projects": result}


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
