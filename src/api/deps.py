from __future__ import annotations

import os
from typing import Optional

from src.insights.storage import DEFAULT_DB_PATH, ProjectInsightsStore


def get_store(db_url: Optional[str] = None) -> ProjectInsightsStore:
    env_url = os.getenv("DATABASE_URL")
    effective = db_url or env_url or f"sqlite:///{DEFAULT_DB_PATH}"
    db_path = effective.replace("sqlite:///", "")

    return ProjectInsightsStore(db_path=db_path)
