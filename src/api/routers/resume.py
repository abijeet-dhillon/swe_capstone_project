from __future__ import annotations

import logging
import shutil
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.api.deps import get_config_manager, get_role_store, get_store
from src.config.config_manager import UserConfig, UserConfigManager
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
    user_id: str = Field(default="default", min_length=1)
    resume_owner_name: Optional[str] = None


class EducationPayload(BaseModel):
    school: str = Field(..., min_length=1)
    degree: str = Field(default="")
    location: str = Field(default="")
    start_date: str = Field(default="")
    end_date: str = Field(default="")
    is_current: bool = False
    expected_graduation: str = Field(default="")


class ResumeProfilePayload(BaseModel):
    user_id: str = Field(default="default", min_length=1)
    resume_owner_name: Optional[str] = None
    project_ids: List[int] = Field(..., min_length=1)
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_label: Optional[str] = None
    github_url: Optional[str] = None
    github_label: Optional[str] = None
    education: List[EducationPayload] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _profile_name(config: UserConfig) -> str:
    if _clean_text(config.name):
        return _clean_text(config.name)
    first = _clean_text(config.first_name)
    last = _clean_text(config.last_name)
    combined = " ".join(part for part in (first, last) if part)
    if combined:
        return combined
    return _clean_text(config.resume_owner_name)


def _profile_education_entries(config: UserConfig) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    if not isinstance(config.education, list):
        return entries
    for raw_entry in config.education:
        if not isinstance(raw_entry, dict):
            continue
        school = _clean_text(raw_entry.get("school"))
        degree = _clean_text(raw_entry.get("degree"))
        location = _clean_text(raw_entry.get("location"))
        start_date = _clean_text(raw_entry.get("from") or raw_entry.get("start_date"))
        end_or_expected = _clean_text(raw_entry.get("to") or raw_entry.get("end_date") or raw_entry.get("expected_graduation"))
        is_current = bool(raw_entry.get("still_studying") or raw_entry.get("is_current"))
        if not any([school, degree, location, start_date, end_or_expected, is_current]):
            continue
        entries.append(
            {
                "school": school,
                "degree": degree,
                "location": location,
                "start_date": start_date,
                "end_date": "" if is_current else end_or_expected,
                "is_current": is_current,
                "expected_graduation": end_or_expected if is_current else "",
            }
        )
    return entries


def _has_meaningful_education_entry(entry: Dict[str, Any]) -> bool:
    school = _clean_text(entry.get("school"))
    if not school:
        return False
    return any(
        [
            _clean_text(entry.get("degree")),
            _clean_text(entry.get("location")),
            _clean_text(entry.get("start_date")),
            _clean_text(entry.get("end_date")),
            _clean_text(entry.get("expected_graduation")),
            bool(entry.get("is_current")),
        ]
    )


def _resume_profile_missing_fields(config: Optional[UserConfig]) -> List[str]:
    if config is None:
        return ["profile"]

    missing: List[str] = []
    if not _profile_name(config):
        missing.append("name")
    if not _clean_text(config.email):
        missing.append("contact.email")

    education_entries = _profile_education_entries(config)
    if not any(_has_meaningful_education_entry(entry) for entry in education_entries):
        missing.append("education")

    return missing


def _build_resume_owner(
    config: UserConfig,
    payload: ResumeProfilePayload,
) -> Dict[str, Any]:
    profile_name = _profile_name(config)
    profile_education = _profile_education_entries(config)
    profile_awards = [item for item in (config.awards or []) if isinstance(item, (str, dict))]

    owner = {
        "name": _clean_text(payload.resume_owner_name) or profile_name,
        "phone": _clean_text(payload.phone) or _clean_text(config.phone_number),
        "email": _clean_text(payload.email) or _clean_text(config.email),
        "linkedin_url": _clean_text(payload.linkedin_url) or _clean_text(config.linkedin_url),
        "linkedin_label": _clean_text(payload.linkedin_label) or _clean_text(config.linkedin_label),
        "github_url": _clean_text(payload.github_url) or _clean_text(config.github_url),
        "github_label": _clean_text(payload.github_label) or _clean_text(config.github_label),
        "education": profile_education,
    }
    if payload.education:
        owner["education"] = [
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
        ]

    if payload.awards:
        owner["awards"] = [award.strip() for award in payload.awards if isinstance(award, str) and award.strip()]
    else:
        owner["awards"] = profile_awards
    return owner


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
    manager: UserConfigManager = Depends(get_config_manager),
):
    user_id = payload.user_id.strip() if isinstance(payload.user_id, str) else ""
    if not user_id:
        raise HTTPException(status_code=422, detail="user_id is required")

    config = manager.load_config(user_id, silent=True)
    missing_fields = _resume_profile_missing_fields(config)
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Resume profile is incomplete. Fill out Profile before generating a resume.",
                "missing_fields": missing_fields,
            },
        )
    if not config:
        raise HTTPException(status_code=404, detail="User configuration not found")

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
        "resume_owner": _build_resume_owner(
            config,
            ResumeProfilePayload(
                user_id=user_id,
                resume_owner_name=payload.resume_owner_name,
                project_ids=[project_id],
            ),
        ),
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
    manager: UserConfigManager = Depends(get_config_manager),
):
    user_id = payload.user_id.strip() if isinstance(payload.user_id, str) else ""
    if not user_id:
        raise HTTPException(status_code=422, detail="user_id is required")

    config = manager.load_config(user_id, silent=True)
    missing_fields = _resume_profile_missing_fields(config)
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Resume profile is incomplete. Fill out Profile before generating a resume.",
                "missing_fields": missing_fields,
            },
        )

    if not config:
        raise HTTPException(status_code=404, detail="User configuration not found")

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

    owner = _build_resume_owner(config, payload)
    report = {
        "resume_owner": owner,
        "awards": owner.get("awards", []),
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
