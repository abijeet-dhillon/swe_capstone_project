"""
Tests for the ProjectFilterEngine: core filtering, sorting, search, and presets.
"""

import sqlite3

import pytest

from src.insights.storage import ProjectInsightsStore
from src.insights.project_filter import (
    DateRange,
    ProjectFilter,
    ProjectFilterEngine,
    ProjectType,
    SortBy,
    SuccessMetrics,
)
from tests.insights.utils import build_pipeline_payload


@pytest.fixture()
def seeded_db(tmp_path):
    db_path = str(tmp_path / "filter_test.db")
    store = ProjectInsightsStore(db_path=db_path, encryption_key=b"test-key")
    payload = build_pipeline_payload()
    store.record_pipeline_run(str(tmp_path / "demo.zip"), payload)
    return db_path


@pytest.fixture()
def engine(seeded_db):
    return ProjectFilterEngine(db_path=seeded_db)


class TestProjectFilterDataclass:
    def test_default_values(self):
        f = ProjectFilter()
        assert f.date_range is None
        assert f.languages == []
        assert f.project_type == ProjectType.ALL
        assert f.sort_by == SortBy.DATE_DESC
        assert f.limit is None
        assert f.offset == 0

    def test_to_dict_roundtrip(self):
        f = ProjectFilter(
            date_range=DateRange(start="2024-01-01", end="2024-12-31"),
            languages=["python"],
            project_type=ProjectType.COLLABORATIVE,
            metrics=SuccessMetrics(min_lines=100, max_commits=500),
            search_text="web app",
            sort_by=SortBy.LOC_DESC,
            limit=10,
            offset=5,
        )
        restored = ProjectFilter.from_dict(f.to_dict())
        assert restored.date_range.start == "2024-01-01"
        assert restored.languages == ["python"]
        assert restored.project_type == ProjectType.COLLABORATIVE
        assert restored.metrics.min_lines == 100
        assert restored.sort_by == SortBy.LOC_DESC
        assert restored.limit == 10

    def test_from_dict_empty(self):
        f = ProjectFilter.from_dict({})
        assert f.project_type == ProjectType.ALL
        assert f.sort_by == SortBy.DATE_DESC


class TestFilterEngineQuery:
    def test_empty_filter_returns_all(self, engine):
        results = engine.apply_filter(ProjectFilter())
        assert len(results) >= 2
        names = {r["project_name"] for r in results}
        assert "ProjectAlpha" in names
        assert "ProjectBeta" in names

    def test_results_contain_expected_fields(self, engine):
        results = engine.apply_filter(ProjectFilter())
        row = results[0]
        for field in ["project_info_id", "project_name", "total_files", "total_lines"]:
            assert field in row

    def test_search_projects_convenience(self, engine):
        results = engine.search_projects("Alpha")
        assert any(r["project_name"] == "ProjectAlpha" for r in results)

    def test_search_no_match(self, engine):
        assert engine.search_projects("zzz_nonexistent_zzz") == []


class TestFilterEngineTextSearch:
    def test_search_by_name(self, engine):
        results = engine.apply_filter(ProjectFilter(search_text="Alpha"))
        assert len(results) >= 1
        assert all("Alpha" in r["project_name"] for r in results)

    def test_search_partial(self, engine):
        results = engine.apply_filter(ProjectFilter(search_text="Project"))
        assert len(results) >= 2


class TestFilterEngineSorting:
    def test_sort_by_name_asc(self, engine):
        results = engine.apply_filter(ProjectFilter(sort_by=SortBy.NAME_ASC))
        names = [r["project_name"] for r in results]
        assert names == sorted(names)

    def test_sort_by_name_desc(self, engine):
        results = engine.apply_filter(ProjectFilter(sort_by=SortBy.NAME_DESC))
        names = [r["project_name"] for r in results]
        assert names == sorted(names, reverse=True)

    def test_sort_by_loc_desc(self, engine):
        results = engine.apply_filter(ProjectFilter(sort_by=SortBy.LOC_DESC))
        if len(results) >= 2:
            lines = [r["total_lines"] for r in results]
            assert lines == sorted(lines, reverse=True)


class TestFilterEngineMetrics:
    def test_filter_min_lines(self, engine):
        all_results = engine.apply_filter(ProjectFilter())
        max_lines = max(r["total_lines"] for r in all_results)
        results = engine.apply_filter(ProjectFilter(metrics=SuccessMetrics(min_lines=max_lines)))
        assert len(results) >= 1
        assert all(r["total_lines"] >= max_lines for r in results)

    def test_filter_max_lines_zero(self, engine):
        results = engine.apply_filter(ProjectFilter(metrics=SuccessMetrics(max_lines=0)))
        assert len(results) == 0

    def test_filter_combined_metrics(self, engine):
        results = engine.apply_filter(ProjectFilter(
            metrics=SuccessMetrics(min_lines=1, min_commits=1),
            sort_by=SortBy.LOC_DESC,
        ))
        for r in results:
            assert r["total_lines"] >= 1
            assert r["total_commits"] >= 1


class TestFilterEnginePagination:
    def test_limit(self, engine):
        results = engine.apply_filter(ProjectFilter(limit=1))
        assert len(results) <= 1

    def test_offset(self, engine):
        all_results = engine.apply_filter(ProjectFilter(sort_by=SortBy.NAME_ASC))
        if len(all_results) >= 2:
            offset_results = engine.apply_filter(ProjectFilter(sort_by=SortBy.NAME_ASC, offset=1))
            assert offset_results[0]["project_name"] == all_results[1]["project_name"]


class TestFilterPresets:
    def test_save_get_delete_lifecycle(self, engine):
        config = ProjectFilter(languages=["python"], sort_by=SortBy.LOC_DESC)
        pid = engine.save_preset("Python Projects", config, description="All Python")
        assert pid > 0

        preset = engine.get_preset(pid)
        assert preset.name == "Python Projects"
        assert preset.filter_config.languages == ["python"]

        assert engine.delete_preset(pid) is True
        assert engine.get_preset(pid) is None

    def test_get_preset_not_found(self, engine):
        assert engine.get_preset(99999) is None

    def test_get_by_name(self, engine):
        engine.save_preset("Demo Search", ProjectFilter(search_text="demo"))
        preset = engine.get_preset_by_name("Demo Search")
        assert preset.filter_config.search_text == "demo"
        assert engine.get_preset_by_name("nonexistent") is None

    def test_list_presets(self, engine):
        engine.save_preset("Preset A", ProjectFilter())
        engine.save_preset("Preset B", ProjectFilter(limit=5))
        names = {p.name for p in engine.list_presets()}
        assert "Preset A" in names and "Preset B" in names

    def test_upsert_by_name(self, engine):
        engine.save_preset("Upsert", ProjectFilter(limit=5))
        engine.save_preset("Upsert", ProjectFilter(limit=10))
        assert engine.get_preset_by_name("Upsert").filter_config.limit == 10
        assert len([p for p in engine.list_presets() if p.name == "Upsert"]) == 1

    def test_delete_nonexistent(self, engine):
        assert engine.delete_preset(99999) is False


class TestPresetTableCreation:
    def test_creates_table_on_init(self, tmp_path):
        db_path = str(tmp_path / "fresh.db")
        ProjectFilterEngine(db_path=db_path)
        with sqlite3.connect(db_path) as conn:
            table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='filter_presets';"
            ).fetchone()
            assert table is not None

    def test_idempotent_creation(self, tmp_path):
        db_path = str(tmp_path / "idem.db")
        ProjectFilterEngine(db_path=db_path)
        ProjectFilterEngine(db_path=db_path)
        with sqlite3.connect(db_path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='filter_presets';"
            ).fetchone()[0]
            assert count == 1
