"""
test_config_manager.py
------------------------
Unit tests for config_manager.py to ensure user configurations are correctly built, saved, and loaded. 
Verifies directory creation, consent file generation, and graceful handling of missing or invalid paths.

Run from root directory with:
    docker compose run --rm backend python3 -m pytest tests/config/test_config_manager.py -v
    or 
    python3 -m pytest tests/config/test_config_manager.py -v

    (Optional) Test coverage with:
        docker compose run --rm backend pytest tests/config/test_config_manager.py --cov=src/config --cov-report=term-missing -v
        * 97% coverage *
"""
# python3 -m pytest tests/config/test_config_manager.py -v
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from src.config import config_manager

# Helper: use a temporary directory to isolate from real data/configs
@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    """Create a temporary config directory and monkeypatch CONFIG_DIR."""
    temp_dir = tmp_path / "data" / "configs"
    monkeypatch.setattr(config_manager, "CONFIG_DIR", temp_dir)
    return temp_dir

# Test: build_user_config() basic structure
def test_build_user_config_creates_consent_files(temp_config_dir):
    user_id = "testuser"
    cfg = config_manager.build_user_config(user_id)

    # Ensure structure correctness
    assert isinstance(cfg, dict)
    assert cfg["user_id"] == user_id
    assert "consent" in cfg
    assert "llm" in cfg["consent"]
    assert "directory" in cfg["consent"]

    # Check that directories and files were created
    user_dir = temp_config_dir / user_id
    consent_dir = user_dir / "consent"

    assert user_dir.exists()
    assert consent_dir.exists()
    assert (consent_dir / "llm.json").exists()
    assert (consent_dir / "directory.json").exists()

# Test: save_config() writes config.json properly
def test_save_config_creates_file(temp_config_dir):
    user_id = "saveuser"
    sample_cfg = {"user_id": user_id, "consent": {}}

    result = config_manager.save_config(sample_cfg, user_id)
    assert result is True

    user_dir = temp_config_dir / user_id
    config_path = user_dir / "config.json"

    assert config_path.exists(), "config.json should exist after saving"

    with open(config_path, "r") as f:
        data = json.load(f)

    assert data["user_id"] == user_id

# Test: load_config() returns correct data when file exists
def test_load_config_returns_data(temp_config_dir):
    user_id = "loaduser"
    user_dir = temp_config_dir / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    config_path = user_dir / "config.json"
    sample = {"user_id": user_id, "consent": {"test": True}}
    with open(config_path, "w") as f:
        json.dump(sample, f)

    loaded = config_manager.load_config(user_id)
    assert loaded["user_id"] == user_id
    assert "consent" in loaded
    assert loaded["consent"]["test"] is True

# Test: load_config() gracefully handles missing file
def test_load_config_missing_file_returns_empty(temp_config_dir, capsys):
    user_id = "nonexistent"
    result = config_manager.load_config(user_id)
    assert result == {}
    out = capsys.readouterr().out
    assert f"No configuration file found for {user_id}" in out

# Test: save_config() gracefully handles invalid path
def test_save_config_invalid_path(monkeypatch, tmp_path):
    # Force CONFIG_DIR to a read-only invalid location
    bad_dir = tmp_path / "no_permission"
    monkeypatch.setattr(config_manager, "CONFIG_DIR", bad_dir)

    # Simulate permission error
    def fake_open(*args, **kwargs):
        raise PermissionError("Cannot open file")

    monkeypatch.setattr("builtins.open", fake_open)

    result = config_manager.save_config({"user_id": "x"}, "x")
    assert result is False

# Test: ensures CONFIG_DIR is created if missing
def test_config_dir_auto_created(tmp_path, monkeypatch):
    test_dir = tmp_path / "fake_data" / "configs"
    monkeypatch.setattr(config_manager, "CONFIG_DIR", test_dir)

    user_id = "auto_user"
    _ = config_manager.build_user_config(user_id)

    assert test_dir.exists(), "CONFIG_DIR should be auto-created"
    assert (test_dir / user_id).exists(), "User subfolder should be created"

# Test: save -> load full cycle integration
def test_save_and_load_integration(temp_config_dir):
    user_id = "integrated_user"
    cfg = config_manager.build_user_config(user_id)
    assert config_manager.save_config(cfg, user_id)

    loaded = config_manager.load_config(user_id)
    assert loaded["user_id"] == user_id
    assert "consent" in loaded

# Test: invalid JSON read gracefully
def test_load_config_with_corrupted_json(temp_config_dir, capsys):
    user_id = "corrupt_user"
    user_dir = temp_config_dir / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    bad_file = user_dir / "config.json"
    bad_file.write_text("{not valid json}")

    result = config_manager.load_config(user_id)
    assert result == {}
    out = capsys.readouterr().out
    assert "Error loading config" in out

def test_run_cli_save_creates_file_and_prints_saved(tmp_path, monkeypatch, capsys):
    """
    run_cli --user-id <id> --save should:
      - build the config
      - write data/configs/<id>/config.json under the patched CONFIG_DIR
      - print 'Saved: True -> ...' to stdout
      - print the JSON (pretty if --pretty is set)
    """
    # Point CONFIG_DIR to a temp location
    temp_config_dir = tmp_path / "data" / "configs"
    monkeypatch.setattr(config_manager, "CONFIG_DIR", temp_config_dir)

    user_id = "cliuser"
    args = ["prog", "--user-id", user_id, "--save", "--pretty"]

    with patch("sys.argv", args):
        config_manager.run_cli()

    # Assert file was created
    config_path = temp_config_dir / user_id / "config.json"
    assert config_path.exists(), "config.json should exist after CLI save"

    # Assert stdout contains 'Saved: True' and JSON
    out = capsys.readouterr().out
    assert "Saved: True" in out
    assert f"{user_id}.json" in out
    # basic sanity check the printed JSON contains the user_id
    assert f"\"user_id\": \"{user_id}\"" in out

def test_run_cli_load_prints_json_when_exists(tmp_path, monkeypatch, capsys):
    """
    run_cli --user-id <id> --load should:
      - read data/configs/<id>/config.json from patched CONFIG_DIR
      - pretty-print the JSON to stdout when --pretty is passed
    """
    # Point CONFIG_DIR to a temp location
    temp_config_dir = tmp_path / "data" / "configs"
    monkeypatch.setattr(config_manager, "CONFIG_DIR", temp_config_dir)

    # Pre-create a config for this user
    user_id = "cliuser_load"
    user_dir = temp_config_dir / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    config_path = user_dir / "config.json"
    sample = {"user_id": user_id, "consent": {"llm": {"consent_given": False}, "directory": {"consent_given": False}}}
    config_path.write_text(json.dumps(sample))

    args = ["prog", "--user-id", user_id, "--load", "--pretty"]

    with patch("sys.argv", args):
        config_manager.run_cli()

    # Assert stdout pretty-printed the JSON and includes user_id
    out = capsys.readouterr().out
    assert f"\"user_id\": \"{user_id}\"" in out
    # Should NOT print the "No config found" message
    assert "No config found" not in out