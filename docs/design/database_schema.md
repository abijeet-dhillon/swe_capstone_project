# User Configuration Database Schema

## Overview
The `UserConfigManager` located in `src/config/config_manager.py` stores CLI-submitted upload information and consent flags in a local SQLite database. The database path is fixed to `sqlite:///data/app.db` (resolved to `data/app.db`). All user-facing helpers (`create_config`, `update_config`, `load_config`, and `save_config_to_db`) go through this schema, so keeping it well documented ensures consistent persistence logic across the project. Tests may override the path by passing `db_path` directly to `UserConfigManager`.

## Table Definition
The schema is initialized on demand via `UserConfigManager.init_db()`. It creates a single normalized table named `user_configurations`.

```sql
CREATE TABLE IF NOT EXISTS user_configurations (
    user_id TEXT PRIMARY KEY,
    zip_file TEXT NOT NULL,
    llm_consent INTEGER NOT NULL,
    llm_consent_asked INTEGER NOT NULL DEFAULT 0,
    data_access_consent INTEGER NOT NULL DEFAULT 0,
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
| `llm_consent_asked` | `INTEGER` | No | Tracks whether LLM consent has been collected (1) or not (0) so we only prompt once. |
| `data_access_consent` | `INTEGER` | No | Stores `1` for data-access consent and `0` otherwise; we prompt once and reuse. |
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

# Insights Storage Schema (Normalized)

## Overview
The insights store is moving from encrypted blob payloads to normalized tables so projects, files, and presentation customizations can be edited independently. The database path remains `sqlite:///data/app.db` (resolved to `data/app.db`). The normalized schema focuses on:

- Incremental ingest: re-adding a ZIP for the same portfolio/resume updates existing projects instead of duplicating them.
- File dedupe: identical files (by content hash) are stored once and reused.
- Presentation controls: per-project selection, ordering, and wording overrides for portfolio and resume items.

## Schema Migrations
`ProjectInsightsStore` should continue to use the `schema_migrations` table and apply the normalized schema as the next migration version.

## `projects` Table

```sql
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id TEXT NOT NULL,
    project_key TEXT NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    project_path TEXT,
    role_title TEXT,
    role_summary TEXT,
    start_date_raw TEXT,
    end_date_raw TEXT,
    start_date_override TEXT,
    end_date_override TEXT,
    chronology_note TEXT,
    skills_detected_json TEXT,
    success_metrics_json TEXT,
    success_feedback TEXT,
    success_evidence TEXT,
    last_source_archive_hash TEXT,
    last_source_archive_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(collection_id, project_key)
);
CREATE INDEX IF NOT EXISTS idx_projects_collection ON projects(collection_id);
```

**Column Highlights**
- `collection_id`: stable identifier for a portfolio/resume dataset (typically the user ID). Incremental ZIPs for the same user reuse this value.
- `project_key`: deterministic identifier (slug/path) used to merge the same project across incremental ingests.
- `start_date_override` / `end_date_override`: user-edited chronology corrections; falls back to raw dates when unset.
- `skills_detected_json`: baseline skills extracted from the project (JSON-encoded list).
- `success_metrics_json`, `success_feedback`, `success_evidence`: evidence of success and validation signals.
- `last_source_archive_hash` / `last_source_archive_path`: last ZIP seen for this project to support incremental history.

The `UNIQUE(collection_id, project_key)` constraint ensures incremental uploads update the existing project row.

## `files` Table

```sql
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    content_hash TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    relative_path TEXT,
    extension TEXT,
    mime_type TEXT,
    size_bytes INTEGER,
    source_archive_hash TEXT,
    source_archive_path TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id);
```

**Column Highlights**
- `content_hash`: SHA-256 of file contents; `UNIQUE(content_hash)` provides global de-dupe.
- `first_seen_at` / `last_seen_at`: track incremental ingestion without duplicating rows.
- `source_archive_hash` / `source_archive_path`: help trace which ZIP last introduced or updated the file.

## `portfolio_insights` Table

```sql
CREATE TABLE IF NOT EXISTS portfolio_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    presentation_type TEXT NOT NULL,
    is_selected INTEGER NOT NULL DEFAULT 1,
    display_order INTEGER,
    title_override TEXT,
    summary_override TEXT,
    role_override TEXT,
    date_range_override TEXT,
    skills_highlighted_json TEXT,
    comparison_attributes_json TEXT,
    evidence_override TEXT,
    resume_bullets_json TEXT,
    display_text TEXT,
    thumbnail_file_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, presentation_type),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(thumbnail_file_id) REFERENCES files(id) ON DELETE SET NULL,
    CHECK (presentation_type IN ('portfolio', 'resume'))
);
CREATE INDEX IF NOT EXISTS idx_portfolio_insights_project ON portfolio_insights(project_id);
```

**Column Highlights**
- `presentation_type`: `portfolio` or `resume` (enforced via CHECK).
- `is_selected` / `display_order`: presentation controls for selection and ordering (ranking).
- `title_override`, `summary_override`, `role_override`, `date_range_override`: user-defined wording for the presentation.
- `skills_highlighted_json`: curated skills to emphasize (JSON-encoded list).
- `comparison_attributes_json`: per-project comparison attributes (JSON-encoded object).
- `resume_bullets_json`: JSON array of resume bullets.
- `display_text`: final rendered text for the chosen presentation.
- `thumbnail_file_id`: project thumbnail; references a row in `files`.

## Foreign Keys and Constraints
- `files.project_id` -> `projects.id` (ON DELETE CASCADE)
- `portfolio_insights.project_id` -> `projects.id` (ON DELETE CASCADE)
- `portfolio_insights.thumbnail_file_id` -> `files.id` (ON DELETE SET NULL)
- `UNIQUE(collection_id, project_key)` in `projects`
- `UNIQUE(content_hash)` in `files`
- `UNIQUE(project_id, presentation_type)` in `portfolio_insights`

## Field Mapping for Presentation Requirements

| Requirement | Fields | Notes |
| --- | --- | --- |
| Incremental ingest for same portfolio/resume | `projects.collection_id`, `projects.project_key`, `files.first_seen_at`, `files.last_seen_at` | Reuse `collection_id` for the same user; `project_key` merges updates. |
| File de-dupe | `files.content_hash` | Ingestion updates `last_seen_at` when a duplicate hash appears. |
| Project re-ranking / ordering | `portfolio_insights.display_order` | Lower numbers appear earlier; can be per presentation type. |
| Project selection for showcase | `portfolio_insights.is_selected` | Toggle inclusion per presentation. |
| Chronology corrections | `projects.start_date_override`, `projects.end_date_override`, `portfolio_insights.date_range_override` | Project-level corrections with optional per-presentation overrides. |
| Skills to highlight | `portfolio_insights.skills_highlighted_json` | JSON list of skills to emphasize. |
| Project comparison attributes | `portfolio_insights.comparison_attributes_json` | JSON object with attributes used in comparisons. |
| User role in project | `projects.role_title`, `projects.role_summary`, `portfolio_insights.role_override` | Base role + per-presentation override. |
| Evidence of success | `projects.success_metrics_json`, `projects.success_feedback`, `projects.success_evidence`, `portfolio_insights.evidence_override` | Supports metrics, feedback, and custom evidence text. |
| Thumbnail association | `portfolio_insights.thumbnail_file_id` | References `files.id`; stable across portfolio/resume with per-presentation flexibility. |
| Portfolio text | `portfolio_insights.display_text`, `title_override`, `summary_override` | Stored under `presentation_type = 'portfolio'`. |
| Resume text + bullets | `portfolio_insights.display_text`, `resume_bullets_json` | Stored under `presentation_type = 'resume'`. |

Whenever the table structure changes, update this section alongside any migration code so the design docs remain authoritative.
