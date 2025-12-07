"""
FastAPI router exposing insights deletion endpoints.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from .storage import ProjectInsightsStore, DEFAULT_DB_PATH

router = APIRouter(prefix="/insights", tags=["insights"])


def get_store(db_url: Optional[str] = None) -> ProjectInsightsStore:
    db_path = (db_url or f"sqlite:///{DEFAULT_DB_PATH}").replace("sqlite:///", "")

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
