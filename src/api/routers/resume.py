from __future__ import annotations

import logging
import shutil
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.api.deps import get_role_store, get_store
from src.insights.storage import ProjectInsightsStore
from src.insights.user_role_store import ProjectRoleStore
from src.pipeline.presentation_pipeline import PresentationPipeline
from src.project.presentation import generate_items_from_project_id
from src.resume.resume_artifact import generate_resume_pdf_artifact

logger = logging.getLogger(__name__)

# Where the portfolio Next.js app serves static files from.
# Keeping this as a constant means only one place needs updating if the
# portfolio-template directory ever moves.
_PORTFOLIO_PUBLIC_DIR = Path(__file__).resolve().parents[3] / "portfolio-template" / "public"
_PORTFOLIO_RESUME_PATH = _PORTFOLIO_PUBLIC_DIR / "resume.pdf"


def _copy_to_portfolio_public(src: Path) -> None:
    """Copy *src* PDF to the portfolio public dir so the Resume button works.

    Fails silently — if the directory doesn't exist or the copy errors out we
    log a warning and move on rather than breaking the resume download.
    """
    try:
        _PORTFOLIO_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, _PORTFOLIO_RESUME_PATH)
        logger.info("Updated portfolio resume at %s", _PORTFOLIO_RESUME_PATH)
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not copy resume to portfolio public dir: %s", exc)


router = APIRouter(prefix="/resume", tags=["resume"])


class ResumeEditPayload(BaseModel):
    bullets: List[str] = Field(default_factory=list)


class ResumePdfPayload(BaseModel):
    resume_owner_name: str = Field(..., min_length=1)


class EducationPayload(BaseModel):
    school: str = Field(..., min_length=1)
    degree: str = Field(default="")
    location: str = Field(default="")
    start_date: str = Field(default="")
    end_date: str = Field(default="")
    is_current: bool = False
    expected_graduation: str = Field(default="")


class ResumeProfilePayload(BaseModel):
    resume_owner_name: str = Field(..., min_length=1)
    project_ids: List[int] = Field(..., min_length=1)
    phone: str = Field(default="")
    email: str = Field(default="")
    linkedin_url: str = Field(default="")
    linkedin_label: str = Field(default="")
    github_url: str = Field(default="")
    github_label: str = Field(default="")
    education: List[EducationPayload] = Field(default_factory=list)


@router.get("/{project_id}")
def get_resume(
    project_id: int,
    store: ProjectInsightsStore = Depends(get_store),
    role_store: ProjectRoleStore = Depends(get_role_store),
):
    payload = store.load_project_insight_by_id(project_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Project not found")
    resume_item = payload.get("resume_item") or {}
    user_role: Optional[str] = None
    metadata = PresentationPipeline(insights_store=store)._get_project_metadata(project_id)
    if metadata:
        user_role = role_store.get_user_role(metadata["zip_hash"], metadata["project_name"])
    if user_role and isinstance(resume_item, dict):
        resume_item = dict(resume_item)
        resume_item["user_role"] = user_role
    return {"project_id": project_id, "user_role": user_role, "resume_item": resume_item}


@router.post("/generate")
def generate_resume(project_id: int, store: ProjectInsightsStore = Depends(get_store)):
    result = generate_items_from_project_id(project_id, store=store, regenerate=True)
  
    resume = result.get("resume_item") or {}
    bullets = list(resume.get("bullets") or [])
    if bullets:
        store.replace_resume_bullets(project_id, bullets)
    return {"project_id": project_id, "resume_item": resume}


@router.post("/{project_id}/pdf")
def generate_resume_pdf(
    project_id: int,
    payload: ResumePdfPayload,
    store: ProjectInsightsStore = Depends(get_store),
):
    generated = generate_items_from_project_id(project_id, store=store, regenerate=True)
    project_payload = dict(generated.get("project_payload") or {})
    if not project_payload:
        raise HTTPException(status_code=404, detail="Project not found")

    resume_item = generated.get("resume_item") or {}
    bullets = list(resume_item.get("bullets") or [])
    if bullets:
        store.replace_resume_bullets(project_id, bullets)

    project_name = (project_payload.get("project_name") or resume_item.get("project_name") or f"project-{project_id}").strip()
    project_payload["resume_item"] = resume_item
    report = {
        "resume_owner": {"name": payload.resume_owner_name.strip()},
        "projects": {project_name: project_payload},
    }

    output_path = Path(tempfile.gettempdir()) / f"resume_project_{project_id}.pdf"
    rendered_path = generate_resume_pdf_artifact(report, output_path)

    # Keep portfolio-template/public/resume.pdf in sync so the Resume button
    # on the generated portfolio site always serves the latest compiled resume.
    _copy_to_portfolio_public(rendered_path)

    filename = f"{project_name.replace(' ', '_')}_resume.pdf"
    return FileResponse(
        path=rendered_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.post("/pdf")
def generate_resume_pdf_bundle(
    payload: ResumeProfilePayload,
    store: ProjectInsightsStore = Depends(get_store),
):
    selected_ids = [int(project_id) for project_id in payload.project_ids if int(project_id) > 0]
    if not selected_ids:
        raise HTTPException(status_code=422, detail="At least one project_id is required")

    ordered_projects: Dict[str, Dict[str, Any]] = {}
    filename_parts: List[str] = []

    for project_id in selected_ids:
        generated = generate_items_from_project_id(project_id, store=store, regenerate=True)
        project_payload = dict(generated.get("project_payload") or {})
        if not project_payload:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        resume_item = generated.get("resume_item") or {}
        bullets = list(resume_item.get("bullets") or [])
        if bullets:
            store.replace_resume_bullets(project_id, bullets)
        project_name = (
            project_payload.get("project_name")
            or resume_item.get("project_name")
            or f"project-{project_id}"
        ).strip()
        filename_parts.append(project_name.replace(" ", "_"))
        project_payload["resume_item"] = resume_item
        ordered_projects[project_name] = project_payload

    owner = {
        "name": payload.resume_owner_name.strip(),
        "phone": payload.phone.strip(),
        "email": payload.email.strip(),
        "linkedin_url": payload.linkedin_url.strip(),
        "linkedin_label": payload.linkedin_label.strip(),
        "github_url": payload.github_url.strip(),
        "github_label": payload.github_label.strip(),
        "education": [
            {
                "school": entry.school.strip(),
                "degree": entry.degree.strip(),
                "location": entry.location.strip(),
                "start_date": entry.start_date.strip(),
                "end_date": entry.end_date.strip(),
                "is_current": bool(entry.is_current),
                "expected_graduation": entry.expected_graduation.strip(),
            }
            for entry in payload.education
            if entry.school.strip()
        ],
    }
    report = {
        "resume_owner": owner,
        "projects": ordered_projects,
        "selected_project_names": list(ordered_projects.keys()),
    }

    output_path = Path(tempfile.gettempdir()) / f"resume_bundle_{'_'.join(str(pid) for pid in selected_ids)}.pdf"
    rendered_path = generate_resume_pdf_artifact(report, output_path)

    # Keep portfolio-template/public/resume.pdf in sync so the Resume button
    # on the generated portfolio site always serves the latest compiled resume.
    _copy_to_portfolio_public(rendered_path)

    filename_stub = owner["name"].replace(" ", "_") or "_".join(filename_parts[:2]) or "resume"
    return FileResponse(
        path=rendered_path,
        media_type="application/pdf",
        filename=f"{filename_stub}_resume.pdf",
    )


@router.post("/{project_id}/edit")
def edit_resume(
    project_id: int,
    payload: ResumeEditPayload,
    store: ProjectInsightsStore = Depends(get_store),
):
    
    changed = store.replace_resume_bullets(project_id, payload.bullets)
    if not changed:
        raise HTTPException(status_code=404, detail="Project not found")
    updated = store.load_project_insight_by_id(project_id)
    return {"status": "ok", "project_id": project_id, "resume_item": updated.get("resume_item")}
