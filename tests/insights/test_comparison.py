import pytest
from src.insights.comparison import ProjectComparison, match_to_job_description


@pytest.fixture
def sample_projects():
    return [
        {"project_name": "Early", "created_at": "2022-01-15", "language": "Python", "key_skills": ["Python"], "total_lines": 500, "test_files": 0, "total_files": 10, "code_files": 10, "documentation_files": 1},
        {"project_name": "Recent", "created_at": "2024-11-10", "language": "Python", "key_skills": ["Python", "Django", "Testing"], "total_lines": 2500, "test_files": 12, "total_files": 40, "code_files": 30, "documentation_files": 5},
    ]


def test_compare_error_on_insufficient():
    assert "error" in ProjectComparison().compare_projects([])


def test_summary_complete(sample_projects):
    result = ProjectComparison().compare_projects(sample_projects)
    assert result["summary"]["total_projects"] == 2
    assert "frameworks" in result["summary"]


def test_skill_evolution(sample_projects):
    result = ProjectComparison().compare_projects(sample_projects)
    assert "Python" in result["skill_evolution"]["consistent_skills"]


def test_quality_improvement(sample_projects):
    result = ProjectComparison().compare_projects(sample_projects)
    assert result["quality_progression"]["improvement_percentage"] > 0


def test_testing_maturity(sample_projects):
    result = ProjectComparison().compare_projects(sample_projects)
    assert result["testing_maturity"]["progression"][0]["maturity"] == "none"


def test_growth_score(sample_projects):
    result = ProjectComparison().compare_projects(sample_projects)
    assert 0 <= result["growth_score"]["score"] <= 100


def test_compare_two(sample_projects):
    result = ProjectComparison().compare_two(sample_projects[0], sample_projects[1])
    assert "skill_diff" in result and "winner" in result


def test_job_matching(sample_projects):
    matches = match_to_job_description(sample_projects, "Python Django developer")
    assert matches[0][0] == "Recent"
    assert "django" in matches[0][2].lower()
