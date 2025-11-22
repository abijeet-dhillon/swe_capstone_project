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

---

# Insights Storage Schema

## Overview
The `ProjectInsightsStore` in `src/insights/storage.py` persists encrypted pipeline output so previously analyzed ZIP files can be revisited without rerunning the entire pipeline. It shares the same SQLite database (`DATABASE_URL`, default `sqlite:///data/app.db`) and maintains two primary tables: `zipfile` (one row per analyzed archive) and `project` (one row per project or `_misc_files`). Serialized payloads are compressed and encrypted before writing to disk, so only derived metadata (counts, hashes, timestamps) is readable directly from SQLite.

## Schema Migrations
`ProjectInsightsStore` bootstraps a `schema_migrations` table and records version `1` the first time it applies the insights schema. Future migrations should append new rows here so the store can upgrade in place.

## `zipfile` Table

```sql
CREATE TABLE IF NOT EXISTS zipfile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zip_hash TEXT UNIQUE NOT NULL,
    zip_path TEXT NOT NULL,
    metadata_hash TEXT NOT NULL,
    metadata_encrypted BLOB NOT NULL,
    total_projects INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_pipeline_version TEXT,
    backup_marker TEXT
);
```

**Column Highlights**
- `zip_hash`: deterministic SHA-256 derived from the filename and ZIP metadata; used as the external identifier.
- `metadata_encrypted`: compressed+encrypted JSON containing `zip_metadata` (file counts, byte totals, etc.).
- `metadata_hash`: SHA-256 of the plaintext metadata, allows for fast change detection without decrypting.
- `total_projects`: denormalized count of associated projects, updated after each pipeline run.
- `backup_marker`: optional timestamp set when `backup()` runs so operators can confirm the DB was copied.

An index isn’t required beyond the implicit uniqueness on `zip_hash` because lookups always filter by that column.

## `project` Table

```sql
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zip_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    slug TEXT NOT NULL,
    project_path TEXT,
    is_git_repo INTEGER NOT NULL DEFAULT 0,
    insight_hash TEXT NOT NULL,
    insights_encrypted BLOB NOT NULL,
    code_files INTEGER NOT NULL DEFAULT 0,
    doc_files INTEGER NOT NULL DEFAULT 0,
    image_files INTEGER NOT NULL DEFAULT 0,
    video_files INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(zip_id) REFERENCES zipfile(id) ON DELETE CASCADE,
    UNIQUE(zip_id, project_name)
);
CREATE INDEX IF NOT EXISTS idx_project_zip ON project(zip_id);
```

**Column Highlights**
- `zip_id`: foreign key linking back to the parent `zipfile` row.
- `project_name`: top-level directory (or `_misc_files` for loose files) as reported by the pipeline.
- `slug`: sanitized version of the name for potential UI routing.
- `insight_hash`: SHA-256 of the plaintext payload (including `zip_id`/`project_name`) used to detect incremental changes.
- `insights_encrypted`: compressed+encrypted JSON containing the full project analysis, categorized file lists, etc.
- `code_files`, `doc_files`, `image_files`, `video_files`: cached counts to support quick dashboards without decrypting payloads.

The `(zip_id, project_name)` unique constraint ensures incremental runs update the existing rows instead of duplicating them.

## Access Patterns
1. **record_pipeline_run** – Upserts `zipfile` metadata, then inserts/updates/deletes `project` rows to reflect the latest pipeline output.
2. **load_project_insight** – Decrypts the stored blob when a consumer needs the full JSON payload for a given `zip_hash` + `project_name`.
3. **list_recent_zipfiles** – Returns lightweight metadata for dashboards or selection prompts without decrypting anything.
4. **get_zip_metadata / list_projects_for_zip** – Helper queries introduced for the retrieval CLI to enumerate available data.
5. **backup / restore / purge_expired_records** – Operational utilities to copy the DB, reload from a backup, or enforce retention policies.

Whenever the table structure changes, update this section alongside any migration code so the design docs remain authoritative.
