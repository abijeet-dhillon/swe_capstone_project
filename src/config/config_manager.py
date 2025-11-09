"""
config_manager.py
-------------------
Responsible for storing and loading user configuration data directly in the SQLite database.

This replaces the previous file-based system (data/configs/{user_id}/config.json)
with a centralized `user_configs` table in the SQLite database.

Run from root directory with:
    docker compose run --rm backend python -m src.config.config_manager --user-id testuser --save --pretty
    or 
    python -m src.config.config_manager --user-id testuser --save --pretty
"""

import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
from src.consent.llm_consent_manager import LLMConsentManager
from src.consent.directory_consent_manager import DirectoryConsentManager

# Database path (Docker or local)
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///data/app.db").replace("sqlite:///", "")


def init_db():
    """Ensure the user_configs table exists in the database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            config_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def save_config_to_db(config: dict, user_id: str) -> bool:
    """Save the user configuration JSON into the SQLite database."""
    try:
        init_db()  # ensure table exists
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_configs (user_id, config_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                config_json = excluded.config_json,
                updated_at = excluded.updated_at;
        """, (user_id, json.dumps(config), datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving config to DB: {e}")
        return False


def load_config_from_db(user_id: str) -> dict:
    """Load user configuration from the SQLite database."""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT config_json FROM user_configs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        else:
            print(f"No configuration found for user_id={user_id}")
            return {}
    except Exception as e:
        print(f"Error loading config from DB: {e}")
        return {}


def build_user_config(user_id: str) -> dict:
    """
    Build a complete user configuration using the LLMConsentManager
    and DirectoryConsentManager.
    """
    consent_dir = Path(f"data/configs/{user_id}/consent")
    consent_dir.mkdir(parents=True, exist_ok=True)

    llm_path = consent_dir / "llm.json"
    dir_path = consent_dir / "directory.json"

    llm_manager = LLMConsentManager(config_path=str(llm_path))
    dir_manager = DirectoryConsentManager(config_path=str(dir_path))

    llm_info = llm_manager.get_consent_info()
    dir_info = dir_manager.get_consent_info()

    config = {
        "user_id": user_id,
        "consent": {
            "llm": llm_info,
            "directory": dir_info
        }
    }

    return config


def run_cli():
    """Command-line interface for building, saving, and loading user configs."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build, save, and load user configs (stored in SQLite)."
    )
    parser.add_argument("--user-id", required=True, help="User identifier.")
    parser.add_argument("--save", action="store_true", help="Save the built config to the database.")
    parser.add_argument("--load", action="store_true", help="Load and print the config from the database.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    if args.load:
        cfg = load_config_from_db(args.user_id)
        if not cfg:
            print(f"No config found for user_id={args.user_id}")
        else:
            print(f"Config found for user_id={args.user_id}")
    else:
        cfg = build_user_config(args.user_id)
        if args.save:
            ok = save_config_to_db(cfg, args.user_id)
            print(f"Config saved to DB for user_id={args.user_id}")

if __name__ == "__main__":
    run_cli()