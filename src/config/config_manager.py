"""
config_manager.py
-------------------
Responsible for storing and loading user configuration files. This will allow for
saving, loading, and vaidating user configuration data in a consistent JSON format
for use across the backend pipeline.

Run from root directory with:
docker compose run --rm backend python -m src.config.config_manager --user-id testuser --save --pretty
    or 
python -m src.config.config_manager --user-id testuser --save --pretty
"""

import json
from pathlib import Path
from src.consent.llm_consent_manager import LLMConsentManager
from src.consent.directory_consent_manager import DirectoryConsentManager

CONFIG_DIR = Path("data/configs")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def save_config(config: dict, user_id: str) -> bool:
    """ Save user configuration to /data/configs/{user_id}.json """
    user_dir = CONFIG_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    config_path = user_dir / "config.json"
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
    
def load_config(user_id: str) -> dict:
    """Load main config.json under the user’s directory."""
    config_path = CONFIG_DIR / user_id / "config.json"
    if not config_path.exists():
        print(f"No configuration file found for {user_id}")
        return {}
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}
    
def build_user_config(user_id: str):
    """
    Build a complete user configuration, with LLM + Directory consent
    stored under data/configs/{user_id}/consent/.
    """
    
    user_dir = CONFIG_DIR / user_id
    consent_dir = user_dir / "consent"
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

# CLI
def run_cli():
    """Command-line interface for building, saving, and loading user configs."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Build, save, and load user configs (with consent)."
    )
    parser.add_argument("--user-id", required=True, help="User identifier (used as filename).")
    parser.add_argument("--save", action="store_true", help="Save the built config to /data/configs/{user_id}.json.")
    parser.add_argument("--load", action="store_true", help="Load and print the config for user_id.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")

    args = parser.parse_args()

    if args.load:
        cfg = load_config(args.user_id)
        if not cfg:
            print(f"No config found for user_id={args.user_id}")
        else:
            print(json.dumps(cfg, indent=4 if args.pretty else None))
    else:
        cfg = build_user_config(args.user_id)
        if args.save:
            ok = save_config(cfg, args.user_id)
            print(f"Saved: {ok} -> /data/configs/{args.user_id}.json")
        print(json.dumps(cfg, indent=4 if args.pretty else None))

if __name__ == "__main__":
    run_cli()