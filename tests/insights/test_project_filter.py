"""
Comprehensive tests for project filtering and search functionality.
Tests the ProjectFilterEngine, filter configurations, and preset management.
"""
import pytest
import sqlite3
import json

from src.insights.project_filter import (
    ProjectFilterEngine,
    ProjectFilter,
    DateRange,
    SuccessMetrics,
    SortBy,
    ProjectType,
)
from src.insights.storage import ProjectInsightsStore


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database using the real insights schema migrations."""
    db_path = tmp_path / "test_filter.db"
    ProjectInsightsStore(db_path=str(db_path), encryption_key=b"test-key")
    return str(db_path)


@pytest.fixture
def sample_projects(temp_db):
    """Populate database with sample projects for testing."""
    with sqlite3.connect(temp_db) as conn:
        ingest_data = (
            1,
            "zip",
            "/tmp/sample.zip",
            "sample.zip",
            "sample-hash",
            5,
            1000,
            500,
            "full",
            "completed",
            "2025-01-01T00:00:00",
            "2025-01-01T00:01:00",
            "2025-01-01T00:01:00",
            "2025-01-01T00:01:00",
        )
        conn.execute(
            """
            INSERT INTO ingest (
                id, source_type, source_path, source_name, source_hash,
                file_count, total_uncompressed_bytes, total_compressed_bytes,
                run_type, status, started_at, finished_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ingest_data,
        )

        # Insert projects
        projects_data = [
            (1, "sample-hash", "python-api", "Python API", "python-api", "/path/1", "2025-01-15T10:00:00", "2025-01-15T10:00:00"),
            (2, "sample-hash", "react-dash", "React Dashboard", "react-dash", "/path/2", "2025-06-20T10:00:00", "2025-06-20T10:00:00"),
            (3, "sample-hash", "ml-model", "ML Model", "ml-model", "/path/3", "2024-12-10T10:00:00", "2024-12-10T10:00:00"),
            (4, "sample-hash", "java-backend", "Java Backend", "java-backend", "/path/4", "2025-03-05T10:00:00", "2025-03-05T10:00:00"),
            (5, "sample-hash", "small-script", "Small Script", "small-script", "/path/5", "2025-07-01T10:00:00", "2025-07-01T10:00:00"),
        ]
        conn.executemany(
            """
            INSERT INTO projects (
                id, source_hash, project_key, project_name, slug, root_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            projects_data
        )

        # Insert project snapshots (latest ingest for a single source_hash)
        project_info_data = [
            (1, 1, 1, "Python API", 0, 50, 2500, 120, 3, 1,
             json.dumps([{"tag_type": "language", "name": "Python"}, {"tag_type": "framework", "name": "FastAPI"}, {"tag_type": "skill", "name": "REST API"}]),
             "2025-01-15T10:00:00", "2025-01-15T10:00:00"),
            (2, 2, 1, "React Dashboard", 0, 80, 5000, 200, 2, 1,
             json.dumps([{"tag_type": "language", "name": "JavaScript"}, {"tag_type": "framework", "name": "React"}]),
             "2025-06-20T10:00:00", "2025-06-20T10:00:00"),
            (3, 3, 1, "ML Model", 0, 30, 1500, 50, 1, 1,
             json.dumps([{"tag_type": "language", "name": "Python"}, {"tag_type": "skill", "name": "Machine Learning"}]),
             "2024-12-10T10:00:00", "2024-12-10T10:00:00"),
            (4, 4, 1, "Java Backend", 0, 100, 8000, 300, 5, 1,
             json.dumps([{"tag_type": "language", "name": "Java"}, {"tag_type": "framework", "name": "Spring"}, {"tag_type": "skill", "name": "REST API"}]),
             "2025-03-05T10:00:00", "2025-03-05T10:00:00"),
            (5, 5, 1, "Small Script", 0, 5, 50, 5, 1, 0,
             json.dumps([{"tag_type": "language", "name": "Python"}]),
             "2025-07-01T10:00:00", "2025-07-01T10:00:00"),
        ]
        conn.executemany(
            """
            INSERT INTO project_info (
                id, project_id, ingest_id, project_name, is_deleted,
                total_files, total_lines, total_commits, total_contributors, is_git_repo,
                tags_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            project_info_data
        )

        # Insert portfolio insights
        portfolio_data = [
            (1, "2025-01-15T10:00:00", "REST API for ecommerce", "Full-featured REST API", "backend", "moderate", 1, "Python API with FastAPI"),
            (2, "2025-06-20T10:00:00", "Admin dashboard", "React dashboard for analytics", "frontend", "moderate", 0, "React dashboard with charts"),
            (3, "2024-12-10T10:00:00", "ML recommendation", "Machine learning model", "data-science", "simple", 0, "Python ML model"),
            (4, "2025-03-05T10:00:00", "Enterprise backend", "Java Spring backend", "backend", "complex", 1, "Large Java backend system"),
            (5, "2025-07-01T10:00:00", "Utility script", "Simple automation script", "script", "simple", 0, "Small Python script"),
        ]
        conn.executemany(
            """
            INSERT INTO portfolio_insights (
                project_info_id, generated_at, tagline, description, project_type,
                complexity, is_collaborative, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            portfolio_data
        )

        conn.commit()

    return temp_db


class TestProjectFilterBasics:
    """Test basic filtering functionality."""
    
    def test_empty_filter_returns_all_projects(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter())
        assert len(results) == 5
    
    def test_filter_by_date_range_start(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(date_range=DateRange(start="2025-01-01")))
        assert len(results) == 4  # Excludes ML Model (2024-12-10)
        assert all("2025" in r["project_created_at"] for r in results)
    
    def test_filter_by_date_range_end(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(date_range=DateRange(end="2025-03-31")))
        assert len(results) == 3  # Python API, ML Model, Java Backend
    
    def test_filter_by_date_range_both(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        filter_config = ProjectFilter(date_range=DateRange(start="2025-01-01", end="2025-06-30"))
        results = engine.apply_filter(filter_config)
        assert len(results) == 3  # Python API, React Dashboard, Java Backend


class TestMetricsFiltering:
    """Test filtering by success metrics."""
    
    def test_filter_by_min_lines(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(metrics=SuccessMetrics(min_lines=1000)))
        assert len(results) == 4  # Excludes Small Script (50 LOC)
        assert all(r["total_lines"] >= 1000 for r in results)
    
    def test_filter_by_max_lines(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(metrics=SuccessMetrics(max_lines=2000)))
        assert len(results) == 2  # ML Model and Small Script
        assert all(r["total_lines"] <= 2000 for r in results)
    
    def test_filter_by_min_max_lines(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        filter_config = ProjectFilter(metrics=SuccessMetrics(min_lines=1000, max_lines=6000))
        results = engine.apply_filter(filter_config)
        assert len(results) == 3  # Python API, React Dashboard, ML Model
    
    def test_filter_by_min_commits(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(metrics=SuccessMetrics(min_commits=100)))
        assert len(results) == 3  # Python API, React Dashboard, Java Backend
        assert all(r["total_commits"] >= 100 for r in results)
    
    def test_filter_by_contributors(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(metrics=SuccessMetrics(min_contributors=2)))
        assert len(results) == 3  # Python API, React Dashboard, Java Backend


class TestProjectTypeFiltering:
    """Test filtering by project type and complexity."""
    
    def test_filter_collaborative_projects(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(project_type=ProjectType.COLLABORATIVE))
        assert len(results) == 2  # Python API and Java Backend
        assert all(r["is_collaborative"] == 1 for r in results)
    
    def test_filter_individual_projects(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(project_type=ProjectType.INDIVIDUAL))
        assert len(results) == 3  # React Dashboard, ML Model, Small Script
        assert all(r["is_collaborative"] == 0 for r in results)
    
    def test_filter_by_complexity(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(complexity="simple"))
        assert len(results) == 2  # ML Model and Small Script


class TestTextSearch:
    """Test full-text search functionality."""
    
    def test_search_by_project_name(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(search_text="API"))
        assert len(results) == 1
        assert "API" in results[0]["project_name"]
    
    def test_search_by_description(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(search_text="dashboard"))
        assert len(results) == 1
        assert "dashboard" in results[0]["description"].lower()
    
    def test_search_case_insensitive(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(search_text="python"))
        assert len(results) >= 2  # Python API and ML Model
    
    def test_search_no_results(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(search_text="nonexistent"))
        assert len(results) == 0


class TestTagFiltering:
    """Test filtering by languages, frameworks, and skills."""
    
    def test_filter_by_language(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(languages=["Python"]))
        assert len(results) == 3  # Python API, ML Model, Small Script
    
    def test_filter_by_multiple_languages(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(languages=["Python", "Java"]))
        assert len(results) == 4  # Python API, ML Model, Java Backend, Small Script
    
    def test_filter_by_framework(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(frameworks=["React"]))
        assert len(results) == 1  # React Dashboard
    
    def test_filter_by_skill(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(skills=["REST API"]))
        assert len(results) == 2  # Python API and Java Backend
    
    def test_filter_by_language_and_framework(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        filter_config = ProjectFilter(languages=["Python"], frameworks=["FastAPI"])
        results = engine.apply_filter(filter_config)
        assert len(results) >= 1  # At least Python API


class TestSorting:
    """Test sorting functionality."""
    
    def test_sort_by_date_desc(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(sort_by=SortBy.DATE_DESC))
        assert results[0]["project_name"] == "Small Script"  # 2025-07-01
        assert results[-1]["project_name"] == "ML Model"     # 2024-12-10
    
    def test_sort_by_date_asc(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(sort_by=SortBy.DATE_ASC))
        assert results[0]["project_name"] == "ML Model"      # 2024-12-10
        assert results[-1]["project_name"] == "Small Script" # 2025-07-01
    
    def test_sort_by_loc_desc(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(sort_by=SortBy.LOC_DESC))
        assert results[0]["project_name"] == "Java Backend"  # 8000 LOC
        assert results[-1]["project_name"] == "Small Script" # 50 LOC
    
    def test_sort_by_commits_desc(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(sort_by=SortBy.COMMITS_DESC))
        assert results[0]["total_commits"] == 300  # Java Backend


class TestPagination:
    """Test limit and offset for pagination."""
    
    def test_limit_results(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(limit=2))
        assert len(results) == 2
    
    def test_offset_results(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.apply_filter(ProjectFilter(limit=2, offset=2))
        assert len(results) == 2
    
    def test_limit_and_offset_together(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        page1 = engine.apply_filter(ProjectFilter(limit=2, offset=0))
        page2 = engine.apply_filter(ProjectFilter(limit=2, offset=2))
        assert page1[0]["project_info_id"] != page2[0]["project_info_id"]


class TestPresetManagement:
    """Test saving, loading, and managing filter presets."""
    
    def test_save_preset(self, temp_db):
        engine = ProjectFilterEngine(temp_db)
        filter_config = ProjectFilter(languages=["Python"], sort_by=SortBy.LOC_DESC)
        preset_id = engine.save_preset("Python Projects", filter_config, "All Python projects")
        assert preset_id > 0
    
    def test_get_preset_by_id(self, temp_db):
        engine = ProjectFilterEngine(temp_db)
        preset_id = engine.save_preset("Test", ProjectFilter(languages=["Python"]))
        preset = engine.get_preset(preset_id)
        assert preset is not None
        assert preset.name == "Test"
        assert preset.filter_config.languages == ["Python"]
    
    def test_get_preset_by_name(self, temp_db):
        engine = ProjectFilterEngine(temp_db)
        engine.save_preset("Complex Projects", ProjectFilter(complexity="complex"))
        preset = engine.get_preset_by_name("Complex Projects")
        assert preset is not None
        assert preset.filter_config.complexity == "complex"
    
    def test_list_presets(self, temp_db):
        engine = ProjectFilterEngine(temp_db)
        engine.save_preset("Preset 1", ProjectFilter(languages=["Python"]))
        engine.save_preset("Preset 2", ProjectFilter(languages=["Java"]))
        presets = engine.list_presets()
        assert len(presets) == 2
    
    def test_update_preset(self, temp_db):
        engine = ProjectFilterEngine(temp_db)
        engine.save_preset("My Preset", ProjectFilter(languages=["Python"]), "First version")
        engine.save_preset("My Preset", ProjectFilter(languages=["Java"]), "Updated version")
        preset = engine.get_preset_by_name("My Preset")
        assert preset.filter_config.languages == ["Java"]
        assert preset.description == "Updated version"
    
    def test_delete_preset(self, temp_db):
        engine = ProjectFilterEngine(temp_db)
        preset_id = engine.save_preset("To Delete", ProjectFilter())
        deleted = engine.delete_preset(preset_id)
        assert deleted is True
        preset = engine.get_preset(preset_id)
        assert preset is None
    
    def test_delete_nonexistent_preset(self, temp_db):
        engine = ProjectFilterEngine(temp_db)
        deleted = engine.delete_preset(99999)
        assert deleted is False


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_sql_injection_protection(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        malicious_input = "'; DROP TABLE projects; --"
        results = engine.apply_filter(ProjectFilter(search_text=malicious_input))
        assert isinstance(results, list)
        # Verify table still exists
        all_results = engine.apply_filter(ProjectFilter())
        assert len(all_results) == 5
    
    def test_filter_with_no_matching_projects(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        filter_config = ProjectFilter(metrics=SuccessMetrics(min_lines=100000))
        results = engine.apply_filter(filter_config)
        assert len(results) == 0
    
    def test_search_projects_convenience_method(self, sample_projects):
        engine = ProjectFilterEngine(sample_projects)
        results = engine.search_projects("Python", limit=10)
        assert isinstance(results, list)
        assert len(results) <= 10
