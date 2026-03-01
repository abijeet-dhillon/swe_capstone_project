from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from src.api.deps import (
    get_config_manager,
    get_role_store,
    get_store,
    get_thumbnail_max_bytes,
    get_thumbnail_root,
)
from src.config.config_manager import UserConfigManager
from src.insights.storage import ProjectInsightsStore
from src.insights.user_role_store import ProjectRoleStore
from src.pipeline.presentation_pipeline import PresentationPipeline

router = APIRouter(prefix="/projects", tags=["projects"])

MAX_ROLE_LENGTH = 120
ALLOWED_THUMBNAIL_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_THUMBNAIL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_THUMBNAIL_EXT_BY_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}
DEFAULT_THUMBNAIL_MIME_BY_EXT = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class ProjectUploadRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    zip_path: str = Field(..., min_length=1)


class ProjectListItem(BaseModel):
    project_id: int
    project_name: str
    zip_hash: str
    is_git_repo: bool
    code_files: int
    doc_files: int
    created_at: str
    updated_at: str


class ProjectRoleUpdatePayload(BaseModel):
    role: str


def _resolve_zip_hash(store: ProjectInsightsStore, zip_path: str) -> Optional[str]:
    runs = store.list_recent_zipfiles(limit=5)
    for run in runs:
        if run.get("zip_path") == zip_path:
            return run.get("zip_hash")
    return runs[0]["zip_hash"] if runs else None


def _normalize_role(role_raw: str) -> str:
    role = (role_raw or "").strip()
    if not role:
        raise HTTPException(status_code=422, detail="role must be a non-empty string")
    if len(role) > MAX_ROLE_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"role cannot exceed {MAX_ROLE_LENGTH} characters",
        )
    return role


def _resolve_project_metadata_or_404(
    store: ProjectInsightsStore,
    project_id: int,
) -> Dict[str, str]:
    metadata = PresentationPipeline(insights_store=store)._get_project_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    return metadata


def _build_thumbnail_response(
    project_id: int,
    thumbnail: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not thumbnail:
        return None
    image_path = thumbnail.get("image_path")
    if not image_path:
        return None
    path_obj = Path(image_path)
    if not path_obj.exists():
        return None
    return {
        "thumbnail_path": str(path_obj),
        "thumbnail_url": f"/projects/{project_id}/thumbnail/content",
        "mime_type": thumbnail.get("mime_type"),
        "size_bytes": path_obj.stat().st_size,
        "created_at": thumbnail.get("created_at"),
    }


@router.post("/upload")
def upload_projects(
    payload: ProjectUploadRequest,
    store: ProjectInsightsStore = Depends(get_store),
    manager: UserConfigManager = Depends(get_config_manager),
):
    user_id = payload.user_id.strip()
    zip_path = payload.zip_path.strip()
    if not user_id or not zip_path:
        raise HTTPException(status_code=400, detail="user_id and zip_path are required")

    config = manager.load_config(user_id, silent=True)
    if not config:
        raise HTTPException(status_code=404, detail="Consent not found for user")
    if not config.data_access_consent:
        raise HTTPException(status_code=403, detail="Data access consent not granted")

    if config.zip_file != zip_path:
        manager.update_config(user_id, zip_file=zip_path)

    use_llm = bool(config.llm_consent and config.llm_consent_asked)

    try:
      
        from src.pipeline.orchestrator import ArtifactPipeline  # type: ignore

        pipeline = ArtifactPipeline(insights_store=store)
        result = pipeline.start(
            zip_path,
            use_llm=use_llm,
            data_access_consent=True,
            prompt_project_names=False,
            git_identifier=config.git_identifier,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Pipeline failed") from exc

    if not result:
        raise HTTPException(status_code=400, detail="Pipeline returned no results")

    zip_hash = _resolve_zip_hash(store, zip_path)
    if not zip_hash:
      
        zip_hash = "unknown"
    project_names = [
        name for name in (result.get("projects") or {}).keys() if name != "_misc_files"
    ]

    return {"status": "ok", "zip_hash": zip_hash, "projects": project_names}


@router.get("", response_model=List[ProjectListItem])
def list_projects(
    store: ProjectInsightsStore = Depends(get_store),
):
    pipeline = PresentationPipeline(insights_store=store)
    projects = pipeline.list_available_projects()
    return [
        {
            "project_id": item["project_id"],
            "project_name": item["project_name"],
            "zip_hash": item["zip_hash"],
            "is_git_repo": item["is_git_repo"],
            "code_files": item["code_files"],
            "doc_files": item["doc_files"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }
        for item in projects
    ]


@router.get("/{project_id}")
def get_project(
    project_id: int,
    store: ProjectInsightsStore = Depends(get_store),
    role_store: ProjectRoleStore = Depends(get_role_store),
):
    payload = store.load_project_insight_by_id(project_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Project not found")

    metadata = _resolve_project_metadata_or_404(store, project_id)
    if metadata:
        user_role = role_store.get_user_role(metadata["zip_hash"], metadata["project_name"])
        if user_role:
            payload = dict(payload)
            payload["user_role"] = user_role
            portfolio_item = payload.get("portfolio_item")
            if isinstance(portfolio_item, dict):
                portfolio_item = dict(portfolio_item)
                portfolio_item["user_role"] = user_role
                payload["portfolio_item"] = portfolio_item
            resume_item = payload.get("resume_item")
            if isinstance(resume_item, dict):
                resume_item = dict(resume_item)
                resume_item["user_role"] = user_role
                payload["resume_item"] = resume_item
    thumbnail = store.get_project_thumbnail(project_id)
    thumbnail_ref = _build_thumbnail_response(project_id, thumbnail)
    if thumbnail_ref:
        payload = dict(payload)
        payload.update(thumbnail_ref)

    return {"project_id": project_id, **payload}


@router.put("/{project_id}/role")
def set_project_role(
    project_id: int,
    payload: ProjectRoleUpdatePayload,
    store: ProjectInsightsStore = Depends(get_store),
    role_store: ProjectRoleStore = Depends(get_role_store),
):
    metadata = _resolve_project_metadata_or_404(store, project_id)
    normalized_role = _normalize_role(payload.role)
    updated = role_store.set_user_role(
        metadata["zip_hash"],
        metadata["project_name"],
        normalized_role,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "user_role": normalized_role}


@router.get("/{project_id}/role")
def get_project_role(
    project_id: int,
    store: ProjectInsightsStore = Depends(get_store),
    role_store: ProjectRoleStore = Depends(get_role_store),
):
    metadata = _resolve_project_metadata_or_404(store, project_id)
    role = role_store.get_user_role(metadata["zip_hash"], metadata["project_name"])
    return {"project_id": project_id, "user_role": role}


@router.post("/{project_id}/thumbnail")
async def upload_project_thumbnail(
    project_id: int,
    file: UploadFile = File(...),
    store: ProjectInsightsStore = Depends(get_store),
    thumbnail_root: Path = Depends(get_thumbnail_root),
    max_bytes: int = Depends(get_thumbnail_max_bytes),
):
    _resolve_project_metadata_or_404(store, project_id)

    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").strip()
    suffix = Path(filename).suffix.lower() if filename else ""
    resolved_mime_type = (
        content_type
        if content_type in ALLOWED_THUMBNAIL_MIME_TYPES
        else DEFAULT_THUMBNAIL_MIME_BY_EXT.get(suffix)
    )
    if not resolved_mime_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Use png, jpg, jpeg, or webp.",
        )

    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max {max_bytes} bytes.",
        )

    extension = DEFAULT_THUMBNAIL_EXT_BY_MIME.get(resolved_mime_type, suffix or ".png")
    if extension not in ALLOWED_THUMBNAIL_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid file extension. Use .png, .jpg, .jpeg, or .webp.",
        )

    existing = store.get_project_thumbnail(project_id)
    project_dir = thumbnail_root / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    file_path = project_dir / f"thumbnail{extension}"

    if existing and existing.get("image_path"):
        old = Path(existing["image_path"])
        if old != file_path and old.exists():
            old.unlink()

    file_path.write_bytes(data)
    persisted = store.upsert_project_thumbnail(
        project_id,
        str(file_path),
        resolved_mime_type,
    )
    if not persisted:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "status": "ok",
        "project_id": project_id,
        "thumbnail_path": str(file_path),
        "thumbnail_url": f"/projects/{project_id}/thumbnail/content",
        "mime_type": resolved_mime_type,
        "size_bytes": len(data),
    }


@router.get("/{project_id}/thumbnail")
def get_project_thumbnail(
    project_id: int,
    store: ProjectInsightsStore = Depends(get_store),
):
    _resolve_project_metadata_or_404(store, project_id)
    thumbnail = store.get_project_thumbnail(project_id)
    thumbnail_ref = _build_thumbnail_response(project_id, thumbnail)
    if not thumbnail_ref:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return {"project_id": project_id, **thumbnail_ref}


@router.get("/{project_id}/thumbnail/content")
def get_project_thumbnail_content(
    project_id: int,
    store: ProjectInsightsStore = Depends(get_store),
):
    from fastapi.responses import FileResponse

    _resolve_project_metadata_or_404(store, project_id)
    thumbnail = store.get_project_thumbnail(project_id)
    thumbnail_ref = _build_thumbnail_response(project_id, thumbnail)
    if not thumbnail_ref:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(
        path=thumbnail_ref["thumbnail_path"],
        media_type=thumbnail_ref.get("mime_type") or "application/octet-stream",
    )


@router.delete("/{project_id}/thumbnail")
def delete_project_thumbnail(
    project_id: int,
    store: ProjectInsightsStore = Depends(get_store),
):
    _resolve_project_metadata_or_404(store, project_id)
    thumbnail = store.get_project_thumbnail(project_id)
    if not thumbnail or not thumbnail.get("image_path"):
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    deleted = store.delete_project_thumbnail(project_id)
    image_path = Path(thumbnail["image_path"])
    if image_path.exists():
        image_path.unlink()
    if image_path.parent.exists() and not any(image_path.parent.iterdir()):
        image_path.parent.rmdir()
    if not deleted:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return {"status": "ok", "project_id": project_id}
