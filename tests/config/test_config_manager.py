"""
test_config_manager.py
------------------------
Unit tests for the new database-backed config_manager.py.

These tests verify:
    - correct creation of the user_configs table
    - successful build, save, and load of user configurations in SQLite
    - graceful handling of missing or invalid records
    - functional CLI interactions (--save and --load)

Run from root directory with:
    docker compose run --rm backend python3 -m pytest tests/config/test_config_manager.py -v
(Optional) Test coverage with:
    docker compose run --rm backend pytest tests/config/test_config_manager.py --cov=src/config --cov-report=term-missing -v
"""

import os
import json
import sqlite3
import tempfile
import pytest
from unittest.mock import patch
from src.config import config_manager


# --------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------
@pytest.fixture
def temp_db(monkeypatch):
    """Provide a temporary SQLite database and patch DB_PATH."""
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    monkeypatch.setattr(config_manager, "DB_PATH", tmp_db.name)
    yield tmp_db.name
    tmp_db.close()
    if os.path.exists(tmp_db.name):
        os.remove(tmp_db.name)


# --------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------

def test_init_db_creates_table(temp_db):
    """Ensure init_db() creates the user_configs table."""
    config_manager.init_db()
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_configs';")
    table = cursor.fetchone()
    conn.close()
    assert table is not None, "user_configs table should exist after init_db()"


def test_save_and_load_config_roundtrip(temp_db):
    """Save a config into the database, then load it back."""
    user_id = "test_user"
    sample_cfg = {"user_id": user_id, "consent": {"llm": {"ok": True}}}

    saved = config_manager.save_config_to_db(sample_cfg, user_id)
    assert saved is True

    loaded = config_manager.load_config_from_db(user_id)
    assert loaded["user_id"] == user_id
    assert loaded["consent"]["llm"]["ok"] is True


def test_load_config_missing_user_returns_empty(temp_db, capsys):
    """Loading a non-existent user returns an empty dict and prints a message."""
    result = config_manager.load_config_from_db("no_user")
    assert result == {}
    out = capsys.readouterr().out
    assert "No configuration" in out


def test_save_config_updates_existing_entry(temp_db):
    """Saving twice with same user_id updates the existing record."""
    user_id = "update_user"
    first = {"user_id": user_id, "consent": {"v": 1}}
    second = {"user_id": user_id, "consent": {"v": 2}}

    config_manager.save_config_to_db(first, user_id)
    config_manager.save_config_to_db(second, user_id)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT config_json FROM user_configs WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    assert json.loads(row[0])["consent"]["v"] == 2


def test_build_user_config_structure(temp_db):
    """Verify build_user_config returns expected structure."""
    user_id = "builder"
    cfg = config_manager.build_user_config(user_id)

    assert isinstance(cfg, dict)
    assert cfg["user_id"] == user_id
    assert "consent" in cfg
    assert "llm" in cfg["consent"]
    assert "directory" in cfg["consent"]


def test_run_cli_save_and_load_from_db(temp_db, capsys):
    """Integration test: CLI --save then --load should work with DB."""
    user_id = "cli_user"

    # First, run CLI with --save
    args_save = ["prog", "--user-id", user_id, "--save", "--pretty"]
    with patch("sys.argv", args_save):
        config_manager.run_cli()
    out_save = capsys.readouterr().out
    assert f"Config saved to DB for user_id={user_id}" in out_save

    # Now, run CLI with --load
    args_load = ["prog", "--user-id", user_id, "--load", "--pretty"]
    with patch("sys.argv", args_load):
        config_manager.run_cli()
    out_load = capsys.readouterr().out
    assert f"Config found for user_id={user_id}" in out_load


def test_load_config_from_corrupted_db_entry(temp_db, capsys):
    """Handles corrupted JSON gracefully."""
    user_id = "broken"
    config_manager.init_db()

    conn = sqlite3.connect(temp_db)
    conn.execute(
        "INSERT INTO user_configs (user_id, config_json, updated_at) VALUES (?, ?, datetime('now'))",
        (user_id, "{not valid json}"),
    )
    conn.commit()
    conn.close()

    result = config_manager.load_config_from_db(user_id)
    assert result == {}
    out = capsys.readouterr().out
    assert "Error loading config" in out