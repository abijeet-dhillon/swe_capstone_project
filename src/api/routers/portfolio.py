from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_role_store, get_store
from src.insights.storage import ProjectInsightsStore
from src.insights.user_role_store import ProjectRoleStore
from src.pipeline.presentation_pipeline import PresentationPipeline

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


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


@router.get("/{project_id}")
def get_portfolio_showcase(
    project_id: int,
    store: ProjectInsightsStore = Depends(get_store),
    role_store: ProjectRoleStore = Depends(get_role_store),
):
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

    success_metrics = payload.get("success_metrics")
    if success_metrics and "error" not in success_metrics:
        response["success_metrics"] = success_metrics

    return response
