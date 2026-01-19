"""
FastAPI router exposing insights endpoints (deletion and customization).
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator

from .storage import ProjectInsightsStore, DEFAULT_DB_PATH

router = APIRouter(prefix="/insights", tags=["insights"])


def get_store(db_url: Optional[str] = None) -> ProjectInsightsStore:
    env_url = os.getenv("DATABASE_URL")
    effective = db_url or env_url or f"sqlite:///{DEFAULT_DB_PATH}"
    db_path = effective.replace("sqlite:///", "")

    return ProjectInsightsStore(db_path=db_path)


@router.delete("/")
def delete_all_insights(store: ProjectInsightsStore = Depends(get_store)):
    counts = store.delete_all()
    return {"status": "ok", **counts}


@router.delete("/zips/{zip_hash}")
def delete_zip_insights(zip_hash: str, store: ProjectInsightsStore = Depends(get_store)):
    counts = store.delete_zip(zip_hash)
    if counts["deleted_zips"] == 0:
        raise HTTPException(status_code=404, detail="zip_hash not found")
    return {"status": "ok", **counts}


@router.delete("/projects/{zip_hash}/{project_name}")
def delete_project_insight(zip_hash: str, project_name: str, store: ProjectInsightsStore = Depends(get_store)):
    counts = store.delete_project(zip_hash, project_name)
    if counts["deleted_projects"] == 0:
        raise HTTPException(status_code=404, detail="project not found")
    return {"status": "ok", **counts}


class PortfolioCustomizationPayload(BaseModel):
    portfolio_fields: Optional[Dict[str, Any]] = Field(default=None)
    resume_bullets: Optional[List[str]] = Field(default=None)

    @validator("resume_bullets")
    def _validate_bullets(cls, v):  # type: ignore[override]
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("resume_bullets must be a list of strings")
        cleaned = []
        for b in v:
            if not isinstance(b, str):
                raise ValueError("All resume bullets must be strings")
            s = b.strip()
            if s:
                cleaned.append(s)
        if len(cleaned) == 0:
            raise ValueError("resume_bullets must contain at least one non-empty string")
        return cleaned


@router.patch("/portfolio/{project_info_id}")
def patch_portfolio_customization(
    project_info_id: int,
    payload: PortfolioCustomizationPayload,
    store: ProjectInsightsStore = Depends(get_store),
):
    # Ensure project exists
    existing = store.load_project_insight_by_id(project_info_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="project_info_id not found")

    # Allow only known portfolio fields
    allowed: Dict[str, Any] = {}
    if payload.portfolio_fields:
        for k in [
            "tagline",
            "description",
            "project_type",
            "complexity",
            "is_collaborative",
            "summary",
            "key_features",
        ]:
            if k in payload.portfolio_fields:
                allowed[k] = payload.portfolio_fields[k]

    changed = store.save_portfolio_customization(
        project_info_id,
        portfolio_fields=allowed if allowed else None,
        resume_bullets=payload.resume_bullets,
    )
    if not changed:
        # Nothing to update
        return {"status": "noop", "project_info_id": project_info_id}

    updated = store.load_project_insight_by_id(project_info_id)
    return {"status": "ok", "project_info_id": project_info_id, "portfolio_item": updated.get("portfolio_item"), "resume_item": updated.get("resume_item")}
