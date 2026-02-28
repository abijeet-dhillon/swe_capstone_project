from __future__ import annotations

import inspect
from typing import List, Optional
import math
from datetime import date
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.deps import get_config_manager, get_role_store, get_store
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


class ProjectUploadRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    zip_path: str = Field(..., min_length=1)
    representation: Optional[ProjectUploadRepresentation] = None


class ProjectListItem(BaseModel):
    project_id: int
    project_name: str
    zip_hash: str
    is_git_repo: bool
    code_files: int
    doc_files: int
    created_at: str
    updated_at: str


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

    return {
        "status": "ok",
        "zip_hash": zip_hash,
        "ingest_id": ingest_id,
        "projects": project_names,
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

    metadata = PresentationPipeline(insights_store=store)._get_project_metadata(project_id)
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

    return {"project_id": project_id, **payload}
