"""LinkedIn integration API endpoints"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.deps import get_store
from src.insights.storage import ProjectInsightsStore
from src.integrations.linkedin_formatter import LinkedInFormatter

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


class LinkedInPreviewResponse(BaseModel):
    """LinkedIn post preview response"""

    project_id: int
    project_name: str
    text: str
    char_count: int
    exceeds_limit: bool
    hashtags: List[str]
    preview: str


class LinkedInFormatOptions(BaseModel):
    """Formatting options for LinkedIn posts"""

    include_hashtags: bool = Field(default=True, description="Include hashtags in the post")
    include_emojis: bool = Field(default=True, description="Include emojis in the post")


@router.get("/preview/{project_id}", response_model=LinkedInPreviewResponse)
def get_linkedin_preview(
    project_id: int,
    include_hashtags: bool = Query(default=True, description="Include hashtags"),
    include_emojis: bool = Query(default=True, description="Include emojis"),
    store: ProjectInsightsStore = Depends(get_store),
):
    """
    Generate LinkedIn post preview for a project.

    Returns formatted text ready to copy-paste into LinkedIn.

    Args:
        project_id: The project ID to generate preview for
        include_hashtags: Whether to include hashtags (default: True)
        include_emojis: Whether to include emojis (default: True)
        store: Project insights store dependency

    Returns:
        LinkedInPreviewResponse with formatted post text

    Raises:
        HTTPException: 404 if project not found or portfolio not generated
    """
    payload = store.load_project_insight_by_id(project_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Project not found")

    portfolio_item = payload.get("portfolio_item")
    if not portfolio_item:
        raise HTTPException(
            status_code=404,
            detail="Portfolio item not generated for this project. Please generate portfolio first.",
        )

    if isinstance(portfolio_item, dict) and "error" in portfolio_item:
        raise HTTPException(
            status_code=404,
            detail=f"Portfolio generation failed: {portfolio_item.get('error')}",
        )

    formatter = LinkedInFormatter()
    result = formatter.format_portfolio_post(
        portfolio_item,
        include_hashtags=include_hashtags,
        include_emojis=include_emojis,
    )

    return LinkedInPreviewResponse(
        project_id=project_id,
        project_name=portfolio_item.get("project_name", "Unknown"),
        **result,
    )


@router.post("/preview/{project_id}/custom", response_model=LinkedInPreviewResponse)
def get_custom_linkedin_preview(
    project_id: int,
    options: LinkedInFormatOptions,
    store: ProjectInsightsStore = Depends(get_store),
):
    """
    Generate LinkedIn post preview with custom formatting options.

    Allows fine-tuning of what's included in the post via request body.

    Args:
        project_id: The project ID to generate preview for
        options: Custom formatting options
        store: Project insights store dependency

    Returns:
        LinkedInPreviewResponse with formatted post text

    Raises:
        HTTPException: 404 if project not found or portfolio not generated
    """
    payload = store.load_project_insight_by_id(project_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Project not found")

    portfolio_item = payload.get("portfolio_item")
    if not portfolio_item:
        raise HTTPException(
            status_code=404,
            detail="Portfolio item not generated for this project. Please generate portfolio first.",
        )

    if isinstance(portfolio_item, dict) and "error" in portfolio_item:
        raise HTTPException(
            status_code=404,
            detail=f"Portfolio generation failed: {portfolio_item.get('error')}",
        )

    formatter = LinkedInFormatter()
    result = formatter.format_portfolio_post(
        portfolio_item,
        include_hashtags=options.include_hashtags,
        include_emojis=options.include_emojis,
    )

    return LinkedInPreviewResponse(
        project_id=project_id,
        project_name=portfolio_item.get("project_name", "Unknown"),
        **result,
    )
