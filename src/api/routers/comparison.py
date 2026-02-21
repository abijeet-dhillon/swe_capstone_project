from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from src.api.deps import get_store
from src.insights.storage import ProjectInsightsStore
from src.insights.comparison import ProjectComparison, match_to_job_description

router = APIRouter(prefix="/compare", tags=["comparison"])


class JobMatchRequest(BaseModel):
    job_description: str
    top_n: int = 3


@router.get("/projects")
def compare_all_projects(user_id: Optional[str] = Query(None), store: ProjectInsightsStore = Depends(get_store)):
    projects = store.list_projects()
    if not projects or len(projects) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 projects for comparison")
    
    comparator = ProjectComparison()
    insights = comparator.compare_projects(projects, user_id)
    return {"status": "success", "projects_analyzed": len(projects), "insights": insights}


@router.post("/projects/{project_id_1}/vs/{project_id_2}")
def compare_two_projects(project_id_1: int, project_id_2: int, store: ProjectInsightsStore = Depends(get_store)):
    project1 = store.load_project_insight(project_id_1)
    project2 = store.load_project_insight(project_id_2)
    
    if not project1 or not project2:
        raise HTTPException(status_code=404, detail="One or both projects not found")
    
    comparator = ProjectComparison()
    comparison = comparator.compare_two(project1, project2)
    
    return {"status": "success", "comparison": comparison}


@router.post("/match-job")
def match_projects_to_job(request: JobMatchRequest, store: ProjectInsightsStore = Depends(get_store)):
    projects = store.list_projects()
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")
    
    matches = match_to_job_description(projects, request.job_description)
    
    top_projects = []
    for project_name, score, reason in matches[:request.top_n]:
        project = next((p for p in projects if p.get('project_name') == project_name), None)
        if project:
            top_projects.append({
                "project_name": project_name,
                "relevance_score": score,
                "matching_reason": reason,
                "key_skills": project.get('key_skills', [])[:5],
                "description": project.get('description', '')[:200],
            })
    
    return {
        "status": "success",
        "top_matches": top_projects,
        "suggestion": f"Showcase these {len(top_projects)} projects for this role",
    }


@router.get("/growth")
def get_growth_trajectory(store: ProjectInsightsStore = Depends(get_store)):
    projects = store.list_projects()
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")
    
    sorted_projects = sorted(projects, key=lambda p: p.get('created_at', p.get('first_commit', '2000-01-01')))
    
    timeline = []
    for idx, project in enumerate(sorted_projects):
        timeline.append({
            "project": project.get('project_name'),
            "date": project.get('created_at', project.get('first_commit')),
            "skills_count": len(project.get('key_skills', [])),
            "quality_score": project.get('quality_score', 50),
            "test_coverage": project.get('test_coverage', 0),
            "lines_of_code": project.get('total_lines', 0),
            "project_number": idx + 1,
        })
    
    comparator = ProjectComparison()
    growth_score = comparator._calculate_growth_score(sorted_projects)
    
    return {"status": "success", "timeline": timeline, "growth_score": growth_score, "chart_ready": True}


@router.get("/recommendations")
def get_recommendations(store: ProjectInsightsStore = Depends(get_store)):
    projects = store.list_projects()
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")
    
    sorted_projects = sorted(projects, key=lambda p: p.get('created_at', p.get('first_commit', '2000-01-01')))
    
    comparator = ProjectComparison()
    recommendations = comparator._generate_recommendations(sorted_projects)
    
    return {"status": "success", "recommendations": recommendations}
