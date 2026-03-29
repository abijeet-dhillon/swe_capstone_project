from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.deps import get_config_manager
from src.config.config_manager import UserConfig, UserConfigManager

router = APIRouter(tags=["privacy"])


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


def _derived_name(config: UserConfig) -> Optional[str]:
    if config.name and config.name.strip():
        return config.name.strip()
    first = (config.first_name or "").strip()
    last = (config.last_name or "").strip()
    combined = " ".join(part for part in (first, last) if part)
    if combined:
        return combined
    if config.resume_owner_name and config.resume_owner_name.strip():
        return config.resume_owner_name.strip()
    return None


def _normalize_education(raw_entries: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_entries, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            continue
        school = _clean_text(str(raw_entry.get("school") or ""))
        location = _clean_text(str(raw_entry.get("location") or ""))
        degree = _clean_text(str(raw_entry.get("degree") or ""))
        from_value = _clean_text(str(raw_entry.get("from") or raw_entry.get("start_date") or ""))
        to_value = _clean_text(str(raw_entry.get("to") or raw_entry.get("end_date") or ""))
        still_studying = bool(raw_entry.get("still_studying") or raw_entry.get("is_current"))
        if not any([school, location, degree, from_value, to_value, still_studying]):
            continue
        normalized.append(
            {
                "school": school or "",
                "location": location or "",
                "degree": degree or "",
                "from": from_value or "",
                "to": to_value or "",
                "still_studying": still_studying,
            }
        )
    return normalized


def _normalize_awards(raw_awards: Any) -> List[Union[str, Dict[str, Any]]]:
    if not isinstance(raw_awards, list):
        return []
    normalized: List[Union[str, Dict[str, Any]]] = []
    for raw_award in raw_awards:
        if isinstance(raw_award, str):
            text = raw_award.strip()
            if text:
                normalized.append(text)
            continue
        if isinstance(raw_award, dict):
            name = _clean_text(str(raw_award.get("name") or ""))
            date = _clean_text(str(raw_award.get("date") or ""))
            organization = _clean_text(str(raw_award.get("organization") or ""))
            bullets_raw = raw_award.get("bullets")
            bullets = []
            if isinstance(bullets_raw, list):
                bullets = [item.strip() for item in bullets_raw if isinstance(item, str) and item.strip()]
            if name or date or organization or bullets:
                normalized.append(
                    {
                        "name": name or "",
                        "date": date or "",
                        "organization": organization or "",
                        "bullets": bullets,
                    }
                )
    return normalized


def _profile_response(config: UserConfig) -> Dict[str, Any]:
    name = _derived_name(config)
    education = _normalize_education(config.education)
    awards_raw = _normalize_awards(config.awards)
    awards: List[str] = []
    for award in awards_raw:
        if isinstance(award, str):
            awards.append(award)
            continue
        if isinstance(award, dict):
            label = _clean_text(str(award.get("name") or ""))
            if label:
                awards.append(label)
    first_name = config.first_name
    last_name = config.last_name
    if (not first_name or not first_name.strip()) and name:
        first_name = name.split(" ", 1)[0]
    if (not last_name or not last_name.strip()) and name and " " in name:
        last_name = name.split(" ", 1)[1]

    return {
        "user_id": config.user_id,
        "name": name,
        "contact": {
            "phone_number": config.phone_number,
            "email": config.email,
            "linkedin_url": config.linkedin_url,
            "github_url": config.github_url,
            "linkedin_label": config.linkedin_label,
            "github_label": config.github_label,
        },
        "education": education,
        "awards": awards,
        "portfolio": {
            "title": config.portfolio_title,
            "about_me": config.portfolio_about_me,
            "years_of_experience": config.portfolio_years_of_experience,
            "open_source_contribution": config.portfolio_open_source_contribution,
        },
        "git_identifier": config.git_identifier,
        # Backward-compatible top-level fields
        "first_name": first_name,
        "last_name": last_name,
        "email": config.email,
        "github_username": config.github_username,
    }


class PrivacyConsentRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    zip_path: str = Field(..., min_length=1)
    llm_consent: bool
    data_access_consent: Optional[bool] = None
    resume_owner_name: Optional[str] = None


class GitIdentifierRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    git_identifier: str = Field(..., min_length=1)


@router.post("/privacy-consent")
def set_privacy_consent(
    payload: PrivacyConsentRequest,
    manager: UserConfigManager = Depends(get_config_manager),
):
    user_id = payload.user_id.strip()
    zip_path = payload.zip_path.strip()
    if not user_id or not zip_path:
        raise HTTPException(status_code=400, detail="user_id and zip_path are required")

    existing = manager.load_config(user_id, silent=True)
    resume_owner_name = payload.resume_owner_name.strip() if isinstance(payload.resume_owner_name, str) else None
    if resume_owner_name == "":
        resume_owner_name = None
    if existing:
        updated = manager.update_config(
            user_id,
            zip_file=zip_path,
            llm_consent=payload.llm_consent,
            llm_consent_asked=True,
            data_access_consent=payload.data_access_consent,
            resume_owner_name=resume_owner_name,
        )
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update consent")
        data_access_consent = (
            payload.data_access_consent
            if payload.data_access_consent is not None
            else existing.data_access_consent
        )
    else:
        data_access_consent = payload.data_access_consent if payload.data_access_consent is not None else False
        created = manager.create_config(
            user_id,
            zip_path,
            payload.llm_consent,
            llm_consent_asked=True,
            data_access_consent=data_access_consent,
            resume_owner_name=resume_owner_name,
        )
        if not created:
            raise HTTPException(status_code=500, detail="Failed to store consent")

    return {
        "status": "ok",
        "user_id": user_id,
        "zip_path": zip_path,
        "llm_consent": payload.llm_consent,
        "data_access_consent": data_access_consent,
        "resume_owner_name": resume_owner_name,
    }


@router.post("/git-identifier")
def set_git_identifier(
    payload: GitIdentifierRequest,
    manager: UserConfigManager = Depends(get_config_manager),
):
    user_id = payload.user_id.strip()
    git_identifier = payload.git_identifier.strip()
    if not user_id or not git_identifier:
        raise HTTPException(status_code=400, detail="user_id and git_identifier are required")

    existing = manager.load_config(user_id, silent=True)
    if not existing:
        raise HTTPException(status_code=404, detail="User configuration not found")

    updated = manager.update_config(user_id, git_identifier=git_identifier)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update git_identifier")

    return {"status": "ok", "user_id": user_id, "git_identifier": git_identifier}


@router.get("/git-identifier/{user_id}")
def get_git_identifier(
    user_id: str,
    manager: UserConfigManager = Depends(get_config_manager),
):
    config = manager.load_config(user_id, silent=True)
    if not config:
        raise HTTPException(status_code=404, detail="User configuration not found")

    return {"user_id": user_id, "git_identifier": config.git_identifier}


class ContactProfilePayload(BaseModel):
    phone_number: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_label: Optional[str] = None
    github_label: Optional[str] = None


class EducationProfilePayload(BaseModel):
    school: Optional[str] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    from_date: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    still_studying: bool = False

    class Config:
        allow_population_by_field_name = True


class PortfolioProfilePayload(BaseModel):
    title: Optional[str] = None
    about_me: Optional[str] = None
    years_of_experience: Optional[str] = None
    open_source_contribution: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    # New structured profile payload
    name: Optional[str] = None
    contact: Optional[ContactProfilePayload] = None
    education: Optional[List[EducationProfilePayload]] = None
    awards: Optional[List[Union[str, Dict[str, Any]]]] = None
    portfolio: Optional[PortfolioProfilePayload] = None

    # Existing fields kept for backward compatibility
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    github_username: Optional[str] = None
    git_identifier: Optional[str] = None


@router.get("/profile/{user_id}")
def get_profile(
    user_id: str,
    manager: UserConfigManager = Depends(get_config_manager),
):
    config = manager.load_config(user_id, silent=True)
    if not config:
        raise HTTPException(status_code=404, detail="User configuration not found")
    return _profile_response(config)


@router.patch("/profile/{user_id}")
def update_profile(
    user_id: str,
    payload: ProfileUpdateRequest,
    manager: UserConfigManager = Depends(get_config_manager),
):
    config = manager.load_config(user_id, silent=True)
    if not config:
        raise HTTPException(status_code=404, detail="User configuration not found")

    update_kwargs: Dict[str, Any] = {}

    if payload.first_name is not None:
        update_kwargs["first_name"] = payload.first_name
    if payload.last_name is not None:
        update_kwargs["last_name"] = payload.last_name
    if payload.email is not None:
        update_kwargs["email"] = payload.email
    if payload.github_username is not None:
        update_kwargs["github_username"] = payload.github_username
    if payload.git_identifier is not None:
        update_kwargs["git_identifier"] = payload.git_identifier

    if payload.name is not None:
        update_kwargs["name"] = payload.name

    if payload.contact is not None:
        update_kwargs["phone_number"] = payload.contact.phone_number
        update_kwargs["linkedin_url"] = payload.contact.linkedin_url
        update_kwargs["github_url"] = payload.contact.github_url
        update_kwargs["linkedin_label"] = payload.contact.linkedin_label
        update_kwargs["github_label"] = payload.contact.github_label
        if payload.contact.email is not None:
            update_kwargs["email"] = payload.contact.email

    if payload.education is not None:
        update_kwargs["education"] = _normalize_education(
            [
                {
                    "school": entry.school,
                    "location": entry.location,
                    "degree": entry.degree,
                    "from": entry.from_date,
                    "to": entry.to,
                    "still_studying": entry.still_studying,
                }
                for entry in payload.education
            ]
        )

    if payload.awards is not None:
        update_kwargs["awards"] = _normalize_awards(payload.awards)

    if payload.portfolio is not None:
        update_kwargs["portfolio_title"] = payload.portfolio.title
        update_kwargs["portfolio_about_me"] = payload.portfolio.about_me
        update_kwargs["portfolio_years_of_experience"] = payload.portfolio.years_of_experience
        update_kwargs["portfolio_open_source_contribution"] = payload.portfolio.open_source_contribution

    updated = manager.update_config(user_id, **update_kwargs)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    refreshed = manager.load_config(user_id, silent=True)
    if not refreshed:
        raise HTTPException(status_code=500, detail="Failed to reload profile")
    return _profile_response(refreshed)
