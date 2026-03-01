from __future__ import annotations

from fastapi import APIRouter

from src.api.routers.portfolio import router as portfolio_router
from src.api.routers.privacy import router as privacy_router
from src.api.routers.projects import router as projects_router
from src.api.routers.chronological import router as chronological_router
from src.api.routers.resume import router as resume_router
from src.api.routers.skills import router as skills_router
from src.api.routers.comparison import router as comparison_router
from src.api.routers.linkedin import router as linkedin_router
from src.insights.api import router as insights_router
from src.insights.user_role_api import router as user_role_router
from src.projects.api import router as thumbnail_router

api_router = APIRouter()
api_router.include_router(privacy_router)
api_router.include_router(projects_router)
api_router.include_router(portfolio_router)
api_router.include_router(chronological_router)
api_router.include_router(resume_router)
api_router.include_router(skills_router)
api_router.include_router(comparison_router)
api_router.include_router(linkedin_router)
api_router.include_router(insights_router)
api_router.include_router(user_role_router)
api_router.include_router(thumbnail_router)

__all__ = ["api_router"]
