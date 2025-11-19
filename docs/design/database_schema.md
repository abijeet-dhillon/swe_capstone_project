# User Configuration Database Schema

## Overview
The `UserConfigManager` located in `src/config/config_manager.py` stores CLI-submitted upload information and consent flags in a local SQLite database. The database path is read from the `DATABASE_URL` environment variable and defaults to `sqlite:///data/app.db` (resolved to `data/app.db`). All user-facing helpers (`create_config`, `update_config`, `load_config`, and `save_config_to_db`) go through this schema, so keeping it well documented ensures consistent persistence logic across the project.

## Table Definition
The schema is initialized on demand via `UserConfigManager.init_db()`. It creates a single normalized table named `user_configurations`.

```sql
CREATE TABLE IF NOT EXISTS user_configurations (
    user_id TEXT PRIMARY KEY,
    zip_file TEXT NOT NULL,
    llm_consent INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT
);
```

### Column Details
| Column      | Type   | Nullable | Constraints / Semantics |
|-------------|--------|----------|-------------------------|
| `user_id`   | `TEXT` | No       | Serves as the primary key; maps 1:1 to the CLI `--user-id` argument. |
| `zip_file`  | `TEXT` | No       | Absolute or relative path to the uploaded ZIP archive for the user. |
| `llm_consent` | `INTEGER` | No | Stores `1` for consent and `0` otherwise. The manager converts Python booleans to ints when persisting and back to booleans when loading. |
| `created_at` | `TEXT` | No | ISO-8601 timestamp (`datetime.now(timezone.utc).isoformat()`) recorded once at creation. |
| `updated_at` | `TEXT` | Yes | ISO-8601 timestamp captured whenever `update_config` runs; remains `NULL` until the first update. |

### Additional Notes
- There are no foreign keys because the table is the authoritative source for user configuration metadata.
- `user_id` uniqueness means multiple uploads for the same user overwrite the existing record instead of creating duplicates.
- The schema purposefully stores timestamps as text to avoid SQLite time zone ambiguity while keeping them human readable.

## Data Lifecycle & Access Patterns
1. **Creation** – `create_config` ensures the user ID does not already exist, assigns a `created_at` timestamp, and persists the initial record.
2. **Updates** – `update_config` patches provided fields, leaves unspecified columns untouched, and stamps `updated_at` with the current UTC timestamp.
3. **Upserts** – `_persist_config` is shared by create/update paths and uses `INSERT ... ON CONFLICT(user_id) DO UPDATE` to guarantee idempotent writes.
4. **Reads** – `load_config` queries a single row by `user_id`, casting the `llm_consent` integer back into a boolean before returning a `UserConfig` dataclass instance.

## Example Record
```json
{
  "user_id": "sample-user",
  "zip_file": "/uploads/sample-user/data.zip",
  "llm_consent": true,
  "created_at": "2024-08-01T12:34:56.123456+00:00",
  "updated_at": "2024-08-15T09:20:10.654321+00:00"
}
```

This document should be kept up to date whenever the `user_configurations` table changes so other teams (data ingestion, privacy/compliance, etc.) can rely on a single description of the persisted state.
