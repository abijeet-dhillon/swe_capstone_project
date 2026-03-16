from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.deps import get_store
from src.insights.storage import ProjectInsightsStore
from src.pipeline.presentation_pipeline import PresentationPipeline

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillsAddPayload(BaseModel):
    project_id: int
    skills: List[str]
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=1000, le=9999)
    timestamp: Optional[str] = None


class SkillsRemovePayload(BaseModel):
    project_id: int
    skills: List[str]


class SkillsEditPayload(BaseModel):
    project_id: int
    old: Optional[str] = None
    new: Optional[str] = None
    skills: Optional[List[str]] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=1000, le=9999)
    timestamp: Optional[str] = None


def _normalize_skills(values: List[Any]) -> List[str]:
    normalized: List[str] = []
    seen: Set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        cleaned = value.strip().casefold()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _resolve_event_timestamp(
    *,
    month: Optional[int] = None,
    year: Optional[int] = None,
    timestamp: Optional[str] = None,
) -> str:
    if timestamp is not None:
        candidate = str(timestamp).strip()
        if not candidate:
            raise HTTPException(status_code=400, detail="'timestamp' must be a non-empty ISO datetime.")
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="'timestamp' must be an ISO datetime string.",
            ) from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()

    if (month is None) != (year is None):
        raise HTTPException(status_code=400, detail="Provide both 'month' and 'year' together.")
    if month is not None and year is not None:
        return datetime(year, month, 1, tzinfo=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def _normalize_timeline_events(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        timestamp = entry.get("timestamp")
        if not isinstance(timestamp, str) or not timestamp:
            continue
        skills = _normalize_skills(entry.get("skills", []) or [])
        if not skills:
            continue
        metadata = entry.get("metadata")
        normalized.append(
            {
                "file": str(entry.get("file") or "manual-entry"),
                "timestamp": timestamp,
                "category": str(entry.get("category") or "manual"),
                "skills": skills,
                "metadata": metadata if isinstance(metadata, dict) else {},
            }
        )
    return normalized


def _project_timeline_for_mutation(project_payload: Dict[str, Any], project_id: int) -> List[Dict[str, Any]]:
    global_insights = project_payload.get("global_insights") or {}
    chronology = global_insights.get("chronological_skills") if isinstance(global_insights, dict) else {}
    if not isinstance(chronology, dict):
        return []
    overrides = chronology.get("project_overrides")
    if isinstance(overrides, dict):
        override = overrides.get(str(project_id))
        if isinstance(override, dict):
            if "timeline" in override:
                return _normalize_timeline_events(override.get("timeline"))
    return _normalize_timeline_events(chronology.get("timeline"))


def _align_timeline_with_skills(
    *,
    existing_timeline: List[Dict[str, Any]],
    target_skills: List[str],
    emphasized_skills: Optional[List[str]] = None,
    event_timestamp: Optional[str] = None,
) -> List[Dict[str, Any]]:
    normalized_target = _normalize_skills(target_skills)
    target_set = set(normalized_target)
    if not target_set:
        return []

    aligned: List[Dict[str, Any]] = []
    seen_in_timeline: Set[str] = set()
    for entry in _normalize_timeline_events(existing_timeline):
        retained_skills = [skill for skill in entry.get("skills", []) if skill in target_set]
        if not retained_skills:
            continue
        seen_in_timeline.update(retained_skills)
        aligned.append({**entry, "skills": retained_skills})

    stamp_skills: List[str] = []
    for skill in _normalize_skills(emphasized_skills or []):
        if skill in target_set and skill not in stamp_skills:
            stamp_skills.append(skill)
    for skill in normalized_target:
        if skill not in seen_in_timeline and skill not in stamp_skills:
            stamp_skills.append(skill)

    if stamp_skills:
        aligned.append(
            {
                "file": "manual-entry",
                "timestamp": event_timestamp or datetime.now(timezone.utc).isoformat(),
                "category": "manual",
                "skills": stamp_skills,
                "metadata": {"source": "skills_api", "type": "mutation"},
            }
        )
    return aligned


def _sync_project_chronology(
    *,
    project_id: int,
    updated_skills: List[str],
    store: ProjectInsightsStore,
    emphasized_skills: Optional[List[str]] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    timestamp: Optional[str] = None,
) -> None:
    payload = store.load_project_insight_by_id(project_id)
    if not payload:
        return
    existing_timeline = _project_timeline_for_mutation(payload, project_id)
    resolved_timestamp: Optional[str] = None
    if emphasized_skills is not None or month is not None or year is not None or timestamp is not None:
        resolved_timestamp = _resolve_event_timestamp(month=month, year=year, timestamp=timestamp)
    updated_timeline = _align_timeline_with_skills(
        existing_timeline=existing_timeline,
        target_skills=updated_skills,
        emphasized_skills=emphasized_skills,
        event_timestamp=resolved_timestamp,
    )
    store.upsert_project_chronology_override(project_id, updated_timeline)


def _load_project_skills_or_404(project_id: int, store: ProjectInsightsStore) -> List[str]:
    load = store.load_project_insight_by_id(project_id)
    if load is None:
        raise HTTPException(status_code=404, detail="Project not found")
    skills = load.get("project_metrics", {}).get("skills", [])
    if not isinstance(skills, list):
        skills = []
    return _normalize_skills(skills)


def _skills_response(project_id: int, skills: List[str]) -> Dict[str, Any]:
    return {"project_id": project_id, "skills": skills}


@router.get("")
def list_skills(store: ProjectInsightsStore = Depends(get_store)) -> List[str]:
    pipeline = PresentationPipeline(insights_store=store)
    projects = pipeline.list_available_projects()
    skills: Set[str] = set()
    for item in projects:
        pid = item.get("project_id")
        if not isinstance(pid, int):
            continue
        payload = store.load_project_insight_by_id(pid)
        if not payload:
            continue
        metrics = payload.get("project_metrics") or {}
        for skill in _normalize_skills(metrics.get("skills", []) or []):
            skills.add(skill)
    return sorted(skills)


@router.get("/year")
def get_skills_by_year(
    year: int = Query(..., ge=1000, le=9999),
    store: ProjectInsightsStore = Depends(get_store),
):
    global_insights = store.load_latest_global_insights() or {}
    chronology = global_insights.get("chronological_skills") or {}
    timeline = chronology.get("timeline") if isinstance(chronology, dict) else []
    if not isinstance(timeline, list):
        timeline = []

    year_str = str(year)
    filtered = [
        entry
        for entry in timeline
        if isinstance(entry, dict)
        and isinstance(entry.get("timestamp"), str)
        and entry["timestamp"][:4] == year_str
    ]
    return {"year": year, "timeline": filtered}


@router.get("/{project_id}")
def get_project_skills(project_id: int, store: ProjectInsightsStore = Depends(get_store)):
    current_skills = _load_project_skills_or_404(project_id, store)
    return _skills_response(project_id, current_skills)


@router.post("/add")
def add_skills(payload: SkillsAddPayload, store: ProjectInsightsStore = Depends(get_store)):
    current_skills = _load_project_skills_or_404(payload.project_id, store)
    updated_skills = _normalize_skills(current_skills + payload.skills)
    store.update_project_skills(payload.project_id, updated_skills)
    _sync_project_chronology(
        project_id=payload.project_id,
        updated_skills=updated_skills,
        store=store,
        emphasized_skills=payload.skills,
        month=payload.month,
        year=payload.year,
        timestamp=payload.timestamp,
    )
    return _skills_response(payload.project_id, updated_skills)


@router.post("/remove")
def remove_skills(payload: SkillsRemovePayload, store: ProjectInsightsStore = Depends(get_store)):
    current_skills = _load_project_skills_or_404(payload.project_id, store)
    to_remove = set(_normalize_skills(payload.skills))
    updated_skills = [skill for skill in current_skills if skill not in to_remove]
    store.update_project_skills(payload.project_id, updated_skills)
    _sync_project_chronology(
        project_id=payload.project_id,
        updated_skills=updated_skills,
        store=store,
    )
    return _skills_response(payload.project_id, updated_skills)


@router.post("/edit")
def edit_skills(payload: SkillsEditPayload, store: ProjectInsightsStore = Depends(get_store)):
    current_skills = _load_project_skills_or_404(payload.project_id, store)

    if payload.skills is not None:
        updated_skills = _normalize_skills(payload.skills)
        store.update_project_skills(payload.project_id, updated_skills)
        _sync_project_chronology(
            project_id=payload.project_id,
            updated_skills=updated_skills,
            store=store,
            emphasized_skills=updated_skills,
            month=payload.month,
            year=payload.year,
            timestamp=payload.timestamp,
        )
        return _skills_response(payload.project_id, updated_skills)

    if payload.old is None or payload.new is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'skills' for replacement or both 'old' and 'new'.",
        )

    old_norm = _normalize_skills([payload.old])
    new_norm = _normalize_skills([payload.new])
    if not old_norm or not new_norm:
        raise HTTPException(status_code=400, detail="'old' and 'new' must be non-empty strings")

    old_skill = old_norm[0]
    new_skill = new_norm[0]
    if old_skill not in current_skills:
        return _skills_response(payload.project_id, current_skills)

    replaced = [new_skill if skill == old_skill else skill for skill in current_skills]
    updated_skills = _normalize_skills(replaced)
    store.update_project_skills(payload.project_id, updated_skills)
    _sync_project_chronology(
        project_id=payload.project_id,
        updated_skills=updated_skills,
        store=store,
        emphasized_skills=[new_skill],
        month=payload.month,
        year=payload.year,
        timestamp=payload.timestamp,
    )
    return _skills_response(payload.project_id, updated_skills)