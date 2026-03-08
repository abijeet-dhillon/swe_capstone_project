from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import inspect
from typing import List, Optional
import math
from datetime import date
from typing import Any, Dict, List, Literal, Optional

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
RepresentationSection = Literal[
    "projects",
    "ranking",
    "chronology",
    "skills",
    "attributes",
    "showcase",
]
RankingCriteria = Literal["score", "recency", "commits", "loc", "impact", "user_contrib"]
ALL_REPRESENTATION_SECTIONS = (
    "projects",
    "ranking",
    "chronology",
    "skills",
    "attributes",
    "showcase",
)
DEFAULT_ATTRIBUTE_FIELDS = (
    "project_name",
    "total_commits",
    "total_lines",
    "languages",
    "frameworks",
    "skills",
)


class RankingRepresentation(BaseModel):
    enabled: bool = True
    criteria: RankingCriteria = "score"
    n: Optional[int] = Field(None, ge=1)
    manual_order: List[str] = Field(default_factory=list)


class ChronologyRepresentation(BaseModel):
    enabled: bool = True


class SkillsRepresentation(BaseModel):
    enabled: bool = True
    highlight: List[str] = Field(default_factory=list)
    suppress: List[str] = Field(default_factory=list)


class AttributesRepresentation(BaseModel):
    enabled: bool = True
    fields: List[str] = Field(default_factory=list)


class ShowcaseRepresentation(BaseModel):
    enabled: bool = True
    selected_projects: List[str] = Field(default_factory=list)


class ProjectUploadRepresentation(BaseModel):
    sections: Optional[List[RepresentationSection]] = None
    ranking: Optional[RankingRepresentation] = None
    chronology: Optional[ChronologyRepresentation] = None
    skills: Optional[SkillsRepresentation] = None
    attributes: Optional[AttributesRepresentation] = None
    showcase: Optional[ShowcaseRepresentation] = None

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
    representation: Optional[ProjectUploadRepresentation] = None


class ProjectUpdateRequest(BaseModel):
    """Request body for incremental ZIP update."""
    user_id: str = Field(..., min_length=1)
    old_zip_hash: str = Field(..., min_length=1, description="Hash of the existing ZIP to update")
    new_zip_path: str = Field(..., min_length=1, description="Path to the new ZIP file")


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
def _model_dump(model: Optional[BaseModel]) -> Dict[str, Any]:
    if model is None:
        return {}
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


def _dedupe_strings(values: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    return ordered


def _resolve_run(store: ProjectInsightsStore, zip_path: str) -> Optional[Dict[str, Any]]:
    runs = store.list_recent_zipfiles(limit=20)
    for run in runs:
        if run.get("zip_path") == zip_path:
            return run
    return runs[0] if runs else None


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


def _resolve_representation(
    representation: Optional[ProjectUploadRepresentation],
    forced_sections: Optional[List[RepresentationSection]] = None,
) -> Dict[str, Any]:
    requested = forced_sections or (
        list(representation.sections)
        if representation and representation.sections
        else list(ALL_REPRESENTATION_SECTIONS)
    )
    sections = _dedupe_strings(requested)
    resolved = {
        "sections": sections,
        "ranking": {"enabled": "ranking" in sections, "criteria": "score", "n": None, "manual_order": []},
        "chronology": {"enabled": "chronology" in sections},
        "skills": {"enabled": "skills" in sections, "highlight": [], "suppress": []},
        "attributes": {
            "enabled": "attributes" in sections,
            "fields": list(DEFAULT_ATTRIBUTE_FIELDS),
        },
        "showcase": {"enabled": "showcase" in sections, "selected_projects": []},
    }
    if not representation:
        return resolved
    for key in ("ranking", "chronology", "skills", "attributes", "showcase"):
        section_value = getattr(representation, key)
        if section_value:
            resolved[key].update(_model_dump(section_value))
    if not resolved["attributes"]["fields"]:
        resolved["attributes"]["fields"] = list(DEFAULT_ATTRIBUTE_FIELDS)
    return resolved


def _recency_days(raw_end: Optional[str]) -> int:
    if not raw_end or not isinstance(raw_end, str):
        return 0
    try:
        return max(0, (date.today() - date.fromisoformat(raw_end.split("T")[0])).days)
    except ValueError:
        return 0


def _project_items(report: Dict[str, Any]) -> List[tuple[str, Dict[str, Any]]]:
    projects = report.get("projects") or {}
    if not isinstance(projects, dict):
        return []
    return [(name, payload) for name, payload in projects.items() if name != "_misc_files" and isinstance(payload, dict)]


def _build_ranking_output(report: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    stored = ((report.get("global_insights") or {}).get("project_ranking") or {})
    summary_lookup = {
        item.get("name"): item
        for item in (stored.get("top_summaries") or [])
        if isinstance(item, dict) and item.get("name")
    }
    entries = []
    for project_name, payload in _project_items(report):
        metrics = payload.get("project_metrics") or {}
        git = payload.get("git_analysis") or {}
        activity = git.get("activity_mix") or {}
        total_activity = sum(int(activity.get(key, 0) or 0) for key in ("code", "test", "doc"))
        code_frac = (int(activity.get("code", 0) or 0) / total_activity) if total_activity else 0.0
        commits = int(git.get("total_commits", metrics.get("total_commits", 0)) or 0)
        loc = int(metrics.get("total_lines", 0) or 0)
        contributors = git.get("contributors") or []
        top_contrib = max((int(item.get("commits", 0) or 0) for item in contributors if isinstance(item, dict)), default=0)
        user_contrib = round((top_contrib / commits), 4) if commits > 0 else 0.0
        recency = _recency_days(git.get("last_commit_at") or metrics.get("duration_end"))
        skills = metrics.get("skills") or []
        is_collab = 1 if (git.get("total_contributors", metrics.get("total_contributors", 0)) or 0) > 1 else 0
        score = round(
            0.35 * math.log1p(loc)
            + 0.35 * math.log1p(commits)
            + 0.20 * len(skills)
            + 0.10 * (1.0 if recency <= 180 else 0.5 if recency <= 365 else 0.1)
            + 0.05 * is_collab,
            4,
        )
        entry = {
            "name": project_name,
            "score": score,
            "summary": (summary_lookup.get(project_name) or {}).get("summary"),
            "user_contrib_score": user_contrib,
            "metrics": {
                "commits": commits,
                "loc": loc,
                "recency_days": recency,
                "languages": metrics.get("languages") or [],
                "duration_days": int(metrics.get("duration_days", git.get("duration_days", 0)) or 0),
            },
            "_impact": round(0.5 * commits + 0.4 * math.sqrt(max(loc, 0)) + 0.1 * (code_frac * 100), 4),
        }
        entries.append(entry)

    criteria = config["criteria"]

    def sort_key(item: Dict[str, Any]):
        if criteria == "recency":
            return (item["metrics"]["recency_days"], -item["metrics"]["commits"], -item["metrics"]["loc"])
        if criteria == "commits":
            return (-item["metrics"]["commits"], -item["score"])
        if criteria == "loc":
            return (-item["metrics"]["loc"], -item["score"])
        if criteria == "impact":
            return (-item["_impact"], -item["score"])
        if criteria == "user_contrib":
            return (-item["user_contrib_score"], -item["metrics"]["commits"], -item["score"])
        return (-item["score"], -item["metrics"]["commits"], -item["metrics"]["loc"])

    ordered = sorted(entries, key=sort_key)
    manual_order = {name: idx for idx, name in enumerate(config.get("manual_order") or [])}
    if manual_order:
        ordered = sorted(
            ordered,
            key=lambda item: (0, manual_order[item["name"]]) if item["name"] in manual_order else (1, sort_key(item)),
        )
    limit = config.get("n")
    if limit is not None:
        ordered = ordered[:limit]
    for rank, entry in enumerate(ordered, start=1):
        entry["rank"] = rank
        entry["criteria"] = criteria
        entry.pop("_impact", None)
    return {"criteria": criteria, "items": ordered, "total_projects_ranked": len(entries)}


def _build_skills_output(report: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    highlighted = {item.casefold(): item for item in config.get("highlight") or []}
    suppressed = {item.casefold() for item in config.get("suppress") or []}
    all_skills: Dict[str, str] = {}
    for _project_name, payload in _project_items(report):
        metrics = payload.get("project_metrics") or {}
        for skill in metrics.get("skills") or []:
            if isinstance(skill, str) and skill.strip():
                all_skills.setdefault(skill.casefold(), skill)
    ordered = []
    for lowered, original in highlighted.items():
        if lowered in all_skills and lowered not in suppressed:
            ordered.append(all_skills[lowered])
    for lowered in sorted(all_skills):
        if lowered in suppressed or lowered in highlighted:
            continue
        ordered.append(all_skills[lowered])
    return {"skills": ordered, "highlighted": [skill for skill in ordered if skill.casefold() in highlighted]}


def _build_attributes_output(report: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    fields = _dedupe_strings(config.get("fields") or list(DEFAULT_ATTRIBUTE_FIELDS))
    items = []
    for project_name, payload in _project_items(report):
        metrics = payload.get("project_metrics") or {}
        git = payload.get("git_analysis") or {}
        portfolio = payload.get("portfolio_item") or {}
        source = {
            "project_name": project_name,
            "total_commits": git.get("total_commits", metrics.get("total_commits")),
            "total_lines": metrics.get("total_lines"),
            "languages": metrics.get("languages"),
            "frameworks": metrics.get("frameworks"),
            "skills": metrics.get("skills"),
            **portfolio,
            **metrics,
        }
        items.append({field: source.get(field) for field in fields})
    return {"fields": fields, "projects": items}


def _build_showcase_output(report: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    selected = _dedupe_strings(config.get("selected_projects") or [])
    items = []
    for project_name, payload in _project_items(report):
        if selected and project_name not in selected:
            continue
        items.append(
            {
                "project_name": project_name,
                "portfolio_item": payload.get("portfolio_item") or {},
                "resume_item": payload.get("resume_item") or {},
            }
        )
    return {"projects": items}


def _represent_report(report: Dict[str, Any], representation: Dict[str, Any]) -> Dict[str, Any]:
    sections = representation["sections"]
    output: Dict[str, Any] = {}
    if "projects" in sections:
        output["projects"] = [name for name, _payload in _project_items(report)]
    if "ranking" in sections and representation["ranking"]["enabled"]:
        output["ranking"] = _build_ranking_output(report, representation["ranking"])
    if "chronology" in sections and representation["chronology"]["enabled"]:
        output["chronology"] = ((report.get("global_insights") or {}).get("chronological_skills") or {})
    if "skills" in sections and representation["skills"]["enabled"]:
        output["skills"] = _build_skills_output(report, representation["skills"])
    if "attributes" in sections and representation["attributes"]["enabled"]:
        output["attributes"] = _build_attributes_output(report, representation["attributes"])
    if "showcase" in sections and representation["showcase"]["enabled"]:
        output["showcase"] = _build_showcase_output(report, representation["showcase"])
    return output


def _run_upload(
    payload: ProjectUploadRequest,
    store: ProjectInsightsStore,
    manager: UserConfigManager,
    forced_sections: Optional[List[RepresentationSection]] = None,
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
        start_kwargs = {
            "use_llm": use_llm,
            "data_access_consent": True,
            "prompt_project_names": False,
        }
        if (
            config.git_identifier is not None
            and "git_identifier" in inspect.signature(pipeline.start).parameters
        ):
            start_kwargs["git_identifier"] = config.git_identifier
        result = pipeline.start(
            zip_path,
            **start_kwargs,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Pipeline failed") from exc

    if not result:
        raise HTTPException(status_code=400, detail="Pipeline returned no results")

    run = _resolve_run(store, zip_path)
    zip_hash = (run or {}).get("zip_hash") or "unknown"
    ingest_id = (run or {}).get("ingest_id") or store.load_latest_ingest_id(zip_hash)
    report = store.load_zip_report(zip_hash) if zip_hash != "unknown" else None
    resolved_representation = _resolve_representation(payload.representation, forced_sections)
    if ingest_id:
        store.save_run_representation(ingest_id, resolved_representation)
    represented_output = _represent_report(report or {"projects": result.get("projects") or {}}, resolved_representation)
    project_names = [name for name in (result.get("projects") or {}).keys() if name != "_misc_files"]
    artifacts = result.get("artifacts")
    resume_tex_path = artifacts.get("resume_tex_path") if isinstance(artifacts, dict) else None

    return {
        "status": "ok",
        "zip_hash": zip_hash,
        "ingest_id": ingest_id,
        "projects": project_names,
        "resume_tex_path": resume_tex_path,
        "representation": resolved_representation,
        "represented_output": represented_output,
    }


@router.post("/upload")
def upload_projects(
    payload: ProjectUploadRequest,
    store: ProjectInsightsStore = Depends(get_store),
    manager: UserConfigManager = Depends(get_config_manager),
):
    return _run_upload(payload, store, manager)

def _section_upload(section: RepresentationSection):
    def endpoint(
        payload: ProjectUploadRequest,
        store: ProjectInsightsStore = Depends(get_store),
        manager: UserConfigManager = Depends(get_config_manager),
    ):
        return _run_upload(payload, store, manager, [section])

    endpoint.__name__ = f"upload_projects_{section}"
    return endpoint


for _section in ("skills", "ranking", "chronology", "attributes", "showcase"):
    router.add_api_route(f"/upload/{_section}", _section_upload(_section), methods=["POST"])


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
@router.post("/update/{old_zip_hash}")
def update_existing_zip(
    old_zip_hash: str,
    payload: ProjectUpdateRequest,
    store: ProjectInsightsStore = Depends(get_store),
    manager: UserConfigManager = Depends(get_config_manager),
):
    """
    Incrementally update an existing ZIP analysis with a new ZIP.

    - Projects unique to the old ZIP are retained.
    - Projects unique to the new ZIP are added.
    - Projects with the same name are replaced by the new ZIP's version.
    """
    user_id = payload.user_id.strip()
    new_zip_path = payload.new_zip_path.strip()

    if not user_id or not new_zip_path:
        raise HTTPException(status_code=400, detail="user_id and new_zip_path are required")

    # Validate old zip exists in DB
    old_projects = store.list_projects_for_zip(old_zip_hash)
    if not old_projects:
        raise HTTPException(
            status_code=404,
            detail=f"No existing analysis found for zip_hash: {old_zip_hash}",
        )

    # Validate user consent
    config = manager.load_config(user_id, silent=True)
    if not config:
        raise HTTPException(status_code=404, detail="Consent not found for user")
    if not config.data_access_consent:
        raise HTTPException(status_code=403, detail="Data access consent not granted")

    # Resolve git_identifier from config
    git_identifier = getattr(config, "git_identifier", None)

    try:
        from src.pipeline.orchestrator import ArtifactPipeline  # type: ignore

        pipeline = ArtifactPipeline(insights_store=store)
        merge_summary = pipeline.incremental_update(
            new_zip_path=new_zip_path,
            old_zip_hash=old_zip_hash,
            git_identifier=git_identifier,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Incremental update failed") from exc

    if merge_summary.get("status") == "cancelled":
        return {"status": "cancelled", "message": merge_summary.get("message", "Update cancelled")}

    return {
        "status": "ok",
        "old_zip_hash": old_zip_hash,
        "new_zip_hash": merge_summary.get("new_zip_hash"),
        "new_only_projects": merge_summary.get("new_only_projects", []),
        "retained_projects": merge_summary.get("retained_projects", []),
        "updated_projects": merge_summary.get("updated_projects", []),
        "total_projects": merge_summary.get("total_projects", 0),
    }
