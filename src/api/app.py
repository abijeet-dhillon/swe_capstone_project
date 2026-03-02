from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.deps import get_store
from src.api.routers import api_router
from src.insights.storage import ProjectInsightsStore
from src.projects.api import router as thumbnail_router

app = FastAPI(title="Project Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(thumbnail_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/runs")
def list_runs(store: ProjectInsightsStore = Depends(get_store)):
    return store.list_recent_zipfiles()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8010)
