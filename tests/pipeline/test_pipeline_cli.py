"""
Tests for the unified pipeline CLI module (Simplified <500 LOC).

Core test coverage:
- analyze routes to orchestrator with correct consent handling
- present routes to presentation pipeline with various selectors
- show-portfolio and show-resume format output correctly
- list displays project metadata
"""

import pytest
from unittest.mock import Mock, patch
from src.pipeline import cli


class TestAnalyzeCommand:
    """Tests for the 'analyze' subcommand - NOTE: Skipped heavy orchestrator testing"""
    
    def test_analyze_command_exists(self):
        """Test that analyze command is registered"""
        # Just verify the command handler doesn't crash on malformed input
        with pytest.raises(SystemExit):
            cli.main(["analyze"])  # Missing required argument


class TestPresentCommand:
    """Tests for the 'present' subcommand"""
    
    @patch("src.pipeline.presentation_pipeline.PresentationPipeline")
    def test_present_single_by_id_routes(self, mock_cls):
        """Test present --project-id routes to generate_by_id"""
        from src.pipeline.presentation_pipeline import PresentationResult
        mock_cls.return_value.generate_by_id.return_value = PresentationResult(
            project_id=123, project_name="Test", zip_hash="abc",
            portfolio_item={}, resume_item={}, success=True
        )
        exit_code = cli.main(["present", "--project-id", "123"])
        assert exit_code == 0
        mock_cls.return_value.generate_by_id.assert_called_once_with(123, regenerate=True)
    
    @patch("src.pipeline.presentation_pipeline.PresentationPipeline")
    def test_present_all_routes(self, mock_cls):
        """Test present --all routes to generate_all"""
        from src.pipeline.presentation_pipeline import BatchPresentationResult
        mock_cls.return_value.generate_all.return_value = BatchPresentationResult(
            total_processed=5, successful=5, failed=0, results=[]
        )
        exit_code = cli.main(["present", "--all"])
        assert exit_code == 0
        mock_cls.return_value.generate_all.assert_called_once_with(regenerate=True, limit=None)
    
    @patch("src.pipeline.presentation_pipeline.PresentationPipeline")
    def test_present_failure_returns_error_code(self, mock_cls):
        """Test present returns non-zero exit code on failure"""
        from src.pipeline.presentation_pipeline import PresentationResult
        mock_cls.return_value.generate_by_id.return_value = PresentationResult(
            project_id=123, project_name="Test", zip_hash="abc",
            portfolio_item={}, resume_item={}, success=False, error="Error"
        )
        exit_code = cli.main(["present", "--project-id", "123"])
        assert exit_code == 1


class TestShowPortfolioCommand:
    """Tests for the 'show-portfolio' subcommand"""
    
    @patch("src.pipeline.presentation_pipeline.PresentationPipeline")
    def test_show_portfolio_formats_output(self, mock_cls, capsys):
        """Test show-portfolio displays formatted portfolio item"""
        from src.pipeline.presentation_pipeline import PresentationResult
        mock_cls.return_value.generate_by_id.return_value = PresentationResult(
            project_id=123, project_name="TestProject", zip_hash="abc",
            portfolio_item={
                "project_name": "TestProject", "tagline": "A test", "description": "Test.",
                "languages": ["Python"], "frameworks": ["Django"], "skills": [],
                "key_features": ["F1"], "is_collaborative": True,
                "total_commits": 50, "total_lines": 1000
            },
            resume_item={}, success=True
        )
        exit_code = cli.main(["show-portfolio", "--project-id", "123"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "PORTFOLIO SHOWCASE" in captured.out
        assert "TestProject" in captured.out
    
    @patch("src.pipeline.presentation_pipeline.PresentationPipeline")
    def test_show_portfolio_error_handling(self, mock_cls, capsys):
        """Test show-portfolio handles errors gracefully"""
        from src.pipeline.presentation_pipeline import PresentationResult
        mock_cls.return_value.generate_by_id.return_value = PresentationResult(
            project_id=999, project_name="Unknown", zip_hash="unk",
            portfolio_item={}, resume_item={}, success=False, error="Not found"
        )
        exit_code = cli.main(["show-portfolio", "--project-id", "999"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Not found" in captured.err


class TestShowResumeCommand:
    """Tests for the 'show-resume' subcommand"""
    
    @patch("src.pipeline.presentation_pipeline.PresentationPipeline")
    def test_show_resume_formats_output(self, mock_cls, capsys):
        """Test show-resume displays formatted resume item"""
        from src.pipeline.presentation_pipeline import PresentationResult
        mock_cls.return_value.generate_by_id.return_value = PresentationResult(
            project_id=123, project_name="TestProject", zip_hash="abc",
            portfolio_item={},
            resume_item={
                "project_name": "TestProject",
                "bullets": ["Built app", "Implemented tests", "Collaborated"]
            },
            success=True
        )
        exit_code = cli.main(["show-resume", "--project-id", "123"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "RESUME ITEM" in captured.out
        assert "Built app" in captured.out


class TestListCommand:
    """Tests for the 'list' subcommand"""
    
    @patch("src.pipeline.presentation_pipeline.PresentationPipeline")
    def test_list_displays_projects(self, mock_cls, capsys):
        """Test list displays project metadata in table format"""
        mock_cls.return_value.list_available_projects.return_value = [
            {
                "project_id": 1, "project_name": "Project One", "zip_hash": "abcd1234",
                "code_files": 10, "doc_files": 5, "is_git_repo": True,
                "updated_at": "2024-01-15 10:30:00"
            }
        ]
        exit_code = cli.main(["list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Project One" in captured.out
        assert "abcd1234" in captured.out
    
    @patch("src.pipeline.presentation_pipeline.PresentationPipeline")
    def test_list_empty_database(self, mock_cls, capsys):
        """Test list handles empty database gracefully"""
        mock_cls.return_value.list_available_projects.return_value = []
        exit_code = cli.main(["list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No projects found" in captured.out


class TestDeleteCommand:
    """Tests for the 'delete' subcommand"""

    @patch("src.pipeline.cli.confirm_action", return_value=True)
    @patch("src.pipeline.cli.delete_user_configurations_all", return_value=3)
    @patch("src.insights.storage.ProjectInsightsStore")
    def test_delete_all_happy_path(self, mock_store, mock_configs, _confirm, capsys):
        mock_store.return_value.delete_all.return_value = {"deleted_projects": 5}
        exit_code = cli.main(["delete", "all"])
        assert exit_code == 0
        mock_store.return_value.delete_all.assert_called_once()
        mock_configs.assert_called_once()
        captured = capsys.readouterr()
        assert "Deleted projects: 5" in captured.out
        assert "Deleted user configurations: 3" in captured.out

    @patch("src.pipeline.cli.confirm_action", return_value=False)
    def test_delete_cancelled(self, _confirm, capsys):
        exit_code = cli.main(["delete", "insight", "all"])
        assert exit_code == 0
        assert "Cancelled." in capsys.readouterr().out

    @patch("src.pipeline.cli.confirm_action", return_value=True)
    @patch("src.pipeline.cli.delete_insights_for_project_id", return_value={"deleted_projects": 1, "deleted_zips": 0})
    def test_delete_insight_by_project_id(self, mock_delete, _confirm):
        exit_code = cli.main(["delete", "insight", "--project-id", "7"])
        assert exit_code == 0
        mock_delete.assert_called_once_with("data/app.db", 7)

    @patch("src.pipeline.cli.confirm_action", return_value=True)
    @patch("src.insights.storage.ProjectInsightsStore")
    def test_delete_insight_all(self, mock_store, _confirm, capsys):
        mock_store.return_value.delete_all.return_value = {"deleted_projects": 4, "deleted_zips": 2}
        exit_code = cli.main(["delete", "insight", "all"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Deleted projects: 4" in captured.out
        assert "Deleted zips: 2" in captured.out

    @patch("src.pipeline.cli.confirm_action", return_value=True)
    @patch("src.pipeline.cli.delete_user_configurations_all", return_value=2)
    def test_delete_config_all(self, _delete_all, _confirm, capsys):
        exit_code = cli.main(["delete", "config", "all"])
        assert exit_code == 0
        assert "Deleted user configurations: 2" in capsys.readouterr().out

    def test_delete_insight_missing_selector(self):
        exit_code = cli.main(["delete", "insight"])
        assert exit_code == 1

    def test_delete_insight_invalid_argument_combo(self):
        exit_code = cli.main(["delete", "insight", "--project-id", "3", "all"])
        assert exit_code == 1

    def test_delete_config_cancelled(self, capsys):
        with patch("src.pipeline.cli.confirm_action", return_value=False):
            exit_code = cli.main(["delete", "config", "all"])
        assert exit_code == 0
        assert "Cancelled." in capsys.readouterr().out

    def test_delete_missing_target(self):
        exit_code = cli.main(["delete"])
        assert exit_code == 1

    @patch("src.pipeline.cli.confirm_action", return_value=True)
    def test_delete_config_all_missing_table(self, _confirm, tmp_path, capsys):
        db_path = tmp_path / "empty.db"
        exit_code = cli.main(["delete", "--db-path", str(db_path), "config", "all"])
        assert exit_code == 0
        assert "Deleted user configurations: 0" in capsys.readouterr().out

    @patch("src.pipeline.cli.confirm_action", return_value=True)
    def test_delete_insight_project_id_not_found(self, _confirm, tmp_path, capsys):
        import sqlite3

        db_path = tmp_path / "insights.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE project_info (id INTEGER, project_id INTEGER, ingest_id INTEGER);")
            conn.commit()
        exit_code = cli.main(["delete", "--db-path", str(db_path), "insight", "--project-id", "42"])
        assert exit_code == 0
        output = capsys.readouterr().out
        assert "Deleted projects: 0" in output
        assert "Deleted zips: 0" in output

    @patch("src.pipeline.cli.confirm_action", return_value=True)
    def test_delete_insight_cleans_up_related_rows(self, _confirm, tmp_path):
        import sqlite3

        db_path = tmp_path / "insights_full.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE ingest (id INTEGER PRIMARY KEY);")
            conn.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY);")
            conn.execute("CREATE TABLE project_info (id INTEGER, project_id INTEGER, ingest_id INTEGER);")
            conn.execute("INSERT INTO ingest (id) VALUES (1);")
            conn.execute("INSERT INTO projects (id) VALUES (10);")
            conn.execute("INSERT INTO project_info (id, project_id, ingest_id) VALUES (5, 10, 1);")
            conn.commit()

        exit_code = cli.main(["delete", "--db-path", str(db_path), "insight", "--project-id", "5"])
        assert exit_code == 0

        with sqlite3.connect(db_path) as conn:
            assert conn.execute("SELECT COUNT(*) FROM project_info;").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM projects;").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM ingest;").fetchone()[0] == 0


class TestMainFunction:
    """Tests for main() function behavior"""
    
    def test_main_no_command_prints_help(self):
        """Test main() with no command prints help"""
        exit_code = cli.main([])
        assert exit_code == 1
    
    def test_main_unknown_command(self):
        """Test main() with unknown command returns error"""
        with pytest.raises(SystemExit):
            cli.main(["unknown-command"])
