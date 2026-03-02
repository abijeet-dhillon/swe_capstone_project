"""
filter.py
---------
FastAPI router for project filtering and search endpoints.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator

from src.api.deps import resolve_db_path
from src.insights.project_filter import (
    DateRange,
    FilterPreset,
    ProjectFilter,
    ProjectFilterEngine,
    ProjectType,
    SortBy,
    SuccessMetrics,
)

router = APIRouter(prefix="/filter", tags=["filter"])


def get_filter_engine(db_url: Optional[str] = None) -> ProjectFilterEngine:
    """Dependency to get filter engine instance."""
    db_path = resolve_db_path(db_url)
    return ProjectFilterEngine(db_path=db_path)


# Request/Response Models

class DateRangeModel(BaseModel):
    """Date range for filtering."""
    start: Optional[str] = Field(None, description="Start date in ISO format (YYYY-MM-DD)")
    end: Optional[str] = Field(None, description="End date in ISO format (YYYY-MM-DD)")

    def to_date_range(self) -> DateRange:
        return DateRange(start=self.start, end=self.end)


class SuccessMetricsModel(BaseModel):
    """Success metric thresholds."""
    min_lines: Optional[int] = Field(None, ge=0, description="Minimum lines of code")
    max_lines: Optional[int] = Field(None, ge=0, description="Maximum lines of code")
    min_commits: Optional[int] = Field(None, ge=0, description="Minimum commits")
    max_commits: Optional[int] = Field(None, ge=0, description="Maximum commits")
    min_contributors: Optional[int] = Field(None, ge=0, description="Minimum contributors")
    max_contributors: Optional[int] = Field(None, ge=0, description="Maximum contributors")
    min_files: Optional[int] = Field(None, ge=0, description="Minimum files")
    max_files: Optional[int] = Field(None, ge=0, description="Maximum files")

    @validator("max_lines")
    def validate_lines(cls, v, values):
        if v is not None and "min_lines" in values and values["min_lines"] is not None:
            if v < values["min_lines"]:
                raise ValueError("max_lines must be >= min_lines")
        return v

    @validator("max_commits")
    def validate_commits(cls, v, values):
        if v is not None and "min_commits" in values and values["min_commits"] is not None:
            if v < values["min_commits"]:
                raise ValueError("max_commits must be >= min_commits")
        return v

    @validator("max_contributors")
    def validate_contributors(cls, v, values):
        if v is not None and "min_contributors" in values and values["min_contributors"] is not None:
            if v < values["min_contributors"]:
                raise ValueError("max_contributors must be >= min_contributors")
        return v

    @validator("max_files")
    def validate_files(cls, v, values):
        if v is not None and "min_files" in values and values["min_files"] is not None:
            if v < values["min_files"]:
                raise ValueError("max_files must be >= min_files")
        return v

    def to_success_metrics(self) -> SuccessMetrics:
        return SuccessMetrics(
            min_lines=self.min_lines,
            max_lines=self.max_lines,
            min_commits=self.min_commits,
            max_commits=self.max_commits,
            min_contributors=self.min_contributors,
            max_contributors=self.max_contributors,
            min_files=self.min_files,
            max_files=self.max_files,
        )


class ProjectFilterRequest(BaseModel):
    """Request model for filtering projects."""
    date_range: Optional[DateRangeModel] = Field(None, description="Filter by date range")
    languages: List[str] = Field(default_factory=list, description="Filter by programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Filter by frameworks")
    skills: List[str] = Field(default_factory=list, description="Filter by skills")
    project_type: ProjectType = Field(ProjectType.ALL, description="Filter by project type")
    complexity: Optional[str] = Field(None, description="Filter by complexity level")
    metrics: Optional[SuccessMetricsModel] = Field(None, description="Filter by success metrics")
    search_text: Optional[str] = Field(None, description="Search in names, descriptions, etc.")
    sort_by: SortBy = Field(SortBy.DATE_DESC, description="Sort order")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Max results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")

    def to_project_filter(self) -> ProjectFilter:
        """Convert to ProjectFilter domain model."""
        return ProjectFilter(
            date_range=self.date_range.to_date_range() if self.date_range else None,
            languages=self.languages,
            frameworks=self.frameworks,
            skills=self.skills,
            project_type=self.project_type,
            complexity=self.complexity,
            metrics=self.metrics.to_success_metrics() if self.metrics else None,
            search_text=self.search_text,
            sort_by=self.sort_by,
            limit=self.limit,
            offset=self.offset,
        )


class ProjectFilterResponse(BaseModel):
    """Response model for filtered projects."""
    total: int = Field(..., description="Total matching projects")
    projects: List[Dict[str, Any]] = Field(..., description="Filtered project list")
    filter_applied: Dict[str, Any] = Field(..., description="Filter configuration used")


class SavePresetRequest(BaseModel):
    """Request model for saving a filter preset."""
    name: str = Field(..., min_length=1, max_length=100, description="Preset name")
    description: Optional[str] = Field(None, max_length=500, description="Preset description")
    filter_config: ProjectFilterRequest = Field(..., description="Filter configuration to save")

    @validator("name")
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v


class PresetResponse(BaseModel):
    """Response model for filter preset."""
    id: int
    name: str
    description: Optional[str]
    filter_config: Dict[str, Any]
    created_at: str
    updated_at: str


class PresetListResponse(BaseModel):
    """Response model for preset list."""
    total: int
    presets: List[PresetResponse]


class SearchResponse(BaseModel):
    """Response model for search results."""
    total: int = Field(..., description="Number of matching projects")
    projects: List[Dict[str, Any]] = Field(..., description="Matching projects")
    search_term: str = Field(..., description="Search term used")


# API Endpoints

@router.post("/", response_model=ProjectFilterResponse)
def filter_projects(
    filter_request: ProjectFilterRequest,
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """
    Apply filter configuration and return matching projects.
    
    Supports filtering by:
    - Date ranges
    - Technologies (languages, frameworks, skills)
    - Project characteristics (type, complexity)
    - Success metrics (LOC, commits, contributors, files)
    - Text search
    
    Results can be sorted and paginated.
    """
    try:
        filter_config = filter_request.to_project_filter()
        projects = engine.apply_filter(filter_config)
        
        return ProjectFilterResponse(
            total=len(projects),
            projects=projects,
            filter_applied=filter_config.to_dict(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter failed: {str(e)}")


@router.get("/presets", response_model=PresetListResponse)
def list_filter_presets(
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """
    List all saved filter presets.
    
    Returns presets ordered by most recently updated.
    """
    try:
        presets = engine.list_presets()
        preset_responses = [
            PresetResponse(
                id=preset.id,
                name=preset.name,
                description=preset.description,
                filter_config=preset.filter_config.to_dict(),
                created_at=preset.created_at,
                updated_at=preset.updated_at,
            )
            for preset in presets
        ]
        
        return PresetListResponse(
            total=len(preset_responses),
            presets=preset_responses,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list presets: {str(e)}")


@router.get("/presets/{preset_id}", response_model=PresetResponse)
def get_filter_preset(
    preset_id: int,
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """
    Get a specific filter preset by ID.
    """
    try:
        preset = engine.get_preset(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        return PresetResponse(
            id=preset.id,
            name=preset.name,
            description=preset.description,
            filter_config=preset.filter_config.to_dict(),
            created_at=preset.created_at,
            updated_at=preset.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preset: {str(e)}")


@router.post("/presets", response_model=PresetResponse)
def save_filter_preset(
    preset_request: SavePresetRequest,
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """
    Save a new filter preset or update existing one by name.
    
    If a preset with the same name exists, it will be updated.
    """
    try:
        filter_config = preset_request.filter_config.to_project_filter()
        preset_id = engine.save_preset(
            name=preset_request.name,
            filter_config=filter_config,
            description=preset_request.description,
        )
        
        saved_preset = engine.get_preset(preset_id)
        if not saved_preset:
            raise HTTPException(status_code=500, detail="Failed to retrieve saved preset")
        
        return PresetResponse(
            id=saved_preset.id,
            name=saved_preset.name,
            description=saved_preset.description,
            filter_config=saved_preset.filter_config.to_dict(),
            created_at=saved_preset.created_at,
            updated_at=saved_preset.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save preset: {str(e)}")


@router.delete("/presets/{preset_id}")
def delete_filter_preset(
    preset_id: int,
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """
    Delete a filter preset by ID.
    """
    try:
        deleted = engine.delete_preset(preset_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        return {"status": "ok", "deleted_preset_id": preset_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete preset: {str(e)}")


@router.post("/presets/{preset_id}/apply", response_model=ProjectFilterResponse)
def apply_filter_preset(
    preset_id: int,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Override limit"),
    offset: int = Query(0, ge=0, description="Override offset"),
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """
    Apply a saved filter preset to get matching projects.
    
    Optionally override pagination parameters (limit, offset).
    """
    try:
        preset = engine.get_preset(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        filter_config = preset.filter_config
        if limit is not None:
            filter_config.limit = limit
        if offset != 0:
            filter_config.offset = offset
        
        projects = engine.apply_filter(filter_config)
        
        return ProjectFilterResponse(
            total=len(projects),
            projects=projects,
            filter_applied=filter_config.to_dict(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply preset: {str(e)}")


@router.get("/search", response_model=SearchResponse)
def search_projects(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=1000, description="Max results"),
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """
    Full-text search across project names, descriptions, taglines, and summaries.
    
    Returns projects sorted by importance (commits + LOC).
    """
    try:
        projects = engine.search_projects(search_text=q.strip(), limit=limit)
        
        return SearchResponse(
            total=len(projects),
            projects=projects,
            search_term=q.strip(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/options")
def get_filter_options(
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """
    Get available filter options (for UI dropdown population).
    
    Returns:
    - Available sort options
    - Project types
    - Complexity levels (if any exist in database)
    """
    return {
        "sort_options": [
            {"value": sort.value, "label": sort.value.replace("_", " ").title()}
            for sort in SortBy
        ],
        "project_types": [
            {"value": pt.value, "label": pt.value.title()}
            for pt in ProjectType
        ],
        "complexity_levels": ["simple", "moderate", "complex"],
    }


@router.get("/skills/trends")
def get_skill_trends(
    skill: str = Query(..., description="Skill to analyze trends for"),
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """Get skill usage trends over time."""
    try:
        trends = engine.get_skill_trends(skill)
        return {
            "skill": skill,
            "trends": trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/skills/progression")
def get_skill_progression(
    engine: ProjectFilterEngine = Depends(get_filter_engine),
):
    """Get skill progression and usage statistics."""
    try:
        progression = engine.get_skill_progression()
        return {
            "progression": progression
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Progression analysis failed: {str(e)}")
