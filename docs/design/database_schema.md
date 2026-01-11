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

# Normalized Insights Storage Schema (Implemented)

## Overview
This replaces the encrypted `zipfile` + `project` blob storage with normalized tables for ingest sources/runs, projects, files, and portfolio insights. The goal is to make all analysis output queryable and to support future upgrades (incremental ingest, file dedupe, portfolio/resume customization, presentation controls) without reworking storage again. This schema is implemented in `src/insights/storage.py` migrations (schema version 4) and used by pipeline persistence + retrieval.

## Schema Migrations
```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
```

## Ingest Sources & Runs (replaces `zipfile`)
```sql
CREATE TABLE IF NOT EXISTS ingest_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL CHECK (source_type IN ('zip', 'dir')),
    source_path TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    file_count INTEGER NOT NULL DEFAULT 0,
    total_uncompressed_bytes INTEGER NOT NULL DEFAULT 0,
    total_compressed_bytes INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(source_hash)
);

CREATE TABLE IF NOT EXISTS ingest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    run_type TEXT NOT NULL CHECK (run_type IN ('full', 'incremental')),
    parent_run_id INTEGER,
    pipeline_version TEXT,
    status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('running', 'completed', 'failed')),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    FOREIGN KEY(source_id) REFERENCES ingest_sources(id) ON DELETE CASCADE,
    FOREIGN KEY(parent_run_id) REFERENCES ingest_runs(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_ingest_runs_source ON ingest_runs(source_id);
```

## Projects & Files
```sql
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    project_key TEXT NOT NULL,
    project_name TEXT NOT NULL,
    slug TEXT NOT NULL,
    root_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(source_id, project_key),
    FOREIGN KEY(source_id) REFERENCES ingest_sources(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    run_id INTEGER NOT NULL,
    project_path TEXT,
    is_git_repo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, run_id),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(run_id) REFERENCES ingest_runs(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_runs_run ON project_runs(run_id);

CREATE TABLE IF NOT EXISTS file_contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    mime_type TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(content_hash)
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    relative_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    extension TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(project_id, relative_path),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS file_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    project_run_id INTEGER NOT NULL,
    content_id INTEGER,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    modified_at TEXT,
    is_binary INTEGER NOT NULL DEFAULT 0 CHECK (is_binary IN (0, 1)),
    is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1)),
    language TEXT,
    category TEXT CHECK (category IN ('code', 'documentation', 'images', 'video', 'other')),
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(content_id) REFERENCES file_contents(id) ON DELETE SET NULL,
    UNIQUE(file_id, project_run_id)
);
CREATE INDEX IF NOT EXISTS idx_file_revisions_project_run ON file_revisions(project_run_id);
```

## Portfolio Insights & Metrics (replaces encrypted project blobs)
```sql
CREATE TABLE IF NOT EXISTS project_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_run_id INTEGER NOT NULL,
    total_files INTEGER NOT NULL DEFAULT 0,
    total_lines INTEGER NOT NULL DEFAULT 0,
    total_commits INTEGER NOT NULL DEFAULT 0,
    total_contributors INTEGER NOT NULL DEFAULT 0,
    activity_code INTEGER NOT NULL DEFAULT 0,
    activity_test INTEGER NOT NULL DEFAULT 0,
    activity_doc INTEGER NOT NULL DEFAULT 0,
    duration_start TEXT,
    duration_end TEXT,
    duration_days INTEGER NOT NULL DEFAULT 0,
    doc_files INTEGER NOT NULL DEFAULT 0,
    doc_words INTEGER NOT NULL DEFAULT 0,
    image_files INTEGER NOT NULL DEFAULT 0,
    video_files INTEGER NOT NULL DEFAULT 0,
    test_files INTEGER NOT NULL DEFAULT 0,
    has_documentation INTEGER NOT NULL DEFAULT 0 CHECK (has_documentation IN (0, 1)),
    has_tests INTEGER NOT NULL DEFAULT 0 CHECK (has_tests IN (0, 1)),
    has_images INTEGER NOT NULL DEFAULT 0 CHECK (has_images IN (0, 1)),
    has_videos INTEGER NOT NULL DEFAULT 0 CHECK (has_videos IN (0, 1)),
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE CASCADE,
    UNIQUE(project_run_id)
);

CREATE TABLE IF NOT EXISTS project_contributors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_run_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    commits INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_contributors_run ON project_contributors(project_run_id);

CREATE TABLE IF NOT EXISTS portfolio_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_run_id INTEGER NOT NULL,
    generated_at TEXT NOT NULL,
    pipeline_version TEXT,
    tagline TEXT,
    description TEXT,
    project_type TEXT,
    complexity TEXT,
    is_collaborative INTEGER NOT NULL DEFAULT 0 CHECK (is_collaborative IN (0, 1)),
    summary TEXT,
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE CASCADE,
    UNIQUE(project_run_id)
);

CREATE TABLE IF NOT EXISTS portfolio_key_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_insight_id INTEGER NOT NULL,
    feature_text TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(portfolio_insight_id) REFERENCES portfolio_insights(id) ON DELETE CASCADE,
    UNIQUE(portfolio_insight_id, display_order)
);

CREATE TABLE IF NOT EXISTS resume_bullets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_insight_id INTEGER NOT NULL,
    bullet_text TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_selected INTEGER NOT NULL DEFAULT 1 CHECK (is_selected IN (0, 1)),
    source TEXT NOT NULL DEFAULT 'generated' CHECK (source IN ('generated', 'manual')),
    FOREIGN KEY(portfolio_insight_id) REFERENCES portfolio_insights(id) ON DELETE CASCADE,
    UNIQUE(portfolio_insight_id, display_order)
);
```

## Tags, Skills, Keywords, Evidence
```sql
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_type TEXT NOT NULL CHECK (tag_type IN ('language', 'framework', 'skill', 'design_pattern', 'keyword', 'tool')),
    name TEXT NOT NULL,
    category TEXT,
    UNIQUE(tag_type, name)
);

CREATE TABLE IF NOT EXISTS project_tags (
    project_run_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'local' CHECK (source IN ('local', 'llm', 'manual')),
    score REAL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_highlighted INTEGER NOT NULL DEFAULT 0 CHECK (is_highlighted IN (0, 1)),
    PRIMARY KEY (project_run_id, tag_id),
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS file_tags (
    file_revision_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    score REAL,
    PRIMARY KEY (file_revision_id, tag_id),
    FOREIGN KEY(file_revision_id) REFERENCES file_revisions(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS skill_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_run_id INTEGER NOT NULL,
    file_revision_id INTEGER,
    tag_id INTEGER NOT NULL,
    evidence_type TEXT NOT NULL,
    location TEXT,
    reasoning TEXT,
    confidence REAL,
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(file_revision_id) REFERENCES file_revisions(id) ON DELETE SET NULL,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE RESTRICT
);
```

## File-Level Metrics (text/image/video analyzers)
```sql
CREATE TABLE IF NOT EXISTS file_metric_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_revision_id INTEGER NOT NULL,
    metric_namespace TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    metric_value_text TEXT,
    metric_value_num REAL,
    metric_unit TEXT,
    FOREIGN KEY(file_revision_id) REFERENCES file_revisions(id) ON DELETE CASCADE,
    UNIQUE(file_revision_id, metric_namespace, metric_key)
);
```

## Ranking & Chronology (global insights)
```sql
CREATE TABLE IF NOT EXISTS ranking_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    criteria TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES ingest_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ranking_results (
    ranking_run_id INTEGER NOT NULL,
    project_run_id INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    score REAL,
    recency_days INTEGER,
    commits INTEGER,
    loc INTEGER,
    duration_days INTEGER,
    PRIMARY KEY (ranking_run_id, project_run_id),
    FOREIGN KEY(ranking_run_id) REFERENCES ranking_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ranking_summaries (
    ranking_run_id INTEGER NOT NULL,
    project_run_id INTEGER NOT NULL,
    summary TEXT NOT NULL,
    PRIMARY KEY (ranking_run_id, project_run_id),
    FOREIGN KEY(ranking_run_id) REFERENCES ranking_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chronology_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    file_revision_id INTEGER,
    event_timestamp TEXT NOT NULL,
    category TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES ingest_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(file_revision_id) REFERENCES file_revisions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS chronology_event_skills (
    event_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (event_id, tag_id),
    FOREIGN KEY(event_id) REFERENCES chronology_events(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS chronology_event_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    metric_key TEXT NOT NULL,
    metric_value_text TEXT,
    metric_value_num REAL,
    FOREIGN KEY(event_id) REFERENCES chronology_events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chronology_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    corrected_timestamp TEXT,
    corrected_category TEXT,
    corrected_notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(event_id) REFERENCES chronology_events(id) ON DELETE CASCADE
);
```

## Thumbnails & Presentation Controls
```sql
CREATE TABLE IF NOT EXISTS thumbnails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_run_id INTEGER,
    file_revision_id INTEGER,
    role TEXT NOT NULL CHECK (role IN ('project', 'portfolio', 'resume', 'file')),
    image_path TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    mime_type TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(file_revision_id) REFERENCES file_revisions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS presentation_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    profile_type TEXT NOT NULL CHECK (profile_type IN ('portfolio', 'resume')),
    profile_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user_configurations(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS profile_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    project_run_id INTEGER,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_selected INTEGER NOT NULL DEFAULT 1 CHECK (is_selected IN (0, 1)),
    override_title TEXT,
    override_tagline TEXT,
    override_description TEXT,
    FOREIGN KEY(profile_id) REFERENCES presentation_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(project_run_id) REFERENCES project_runs(id) ON DELETE SET NULL,
    UNIQUE(profile_id, project_id)
);

CREATE TABLE IF NOT EXISTS profile_resume_bullets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_project_id INTEGER NOT NULL,
    resume_bullet_id INTEGER,
    custom_text TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_selected INTEGER NOT NULL DEFAULT 1 CHECK (is_selected IN (0, 1)),
    FOREIGN KEY(profile_project_id) REFERENCES profile_projects(id) ON DELETE CASCADE,
    FOREIGN KEY(resume_bullet_id) REFERENCES resume_bullets(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS profile_project_tags (
    profile_project_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_selected INTEGER NOT NULL DEFAULT 1 CHECK (is_selected IN (0, 1)),
    override_label TEXT,
    PRIMARY KEY (profile_project_id, tag_id),
    FOREIGN KEY(profile_project_id) REFERENCES profile_projects(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS presentation_controls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    control_key TEXT NOT NULL,
    control_value TEXT,
    FOREIGN KEY(profile_id) REFERENCES presentation_profiles(id) ON DELETE CASCADE,
    UNIQUE(profile_id, control_key)
);
```

## Field Mapping (current analysis output -> normalized storage)
| Analysis Output | Source Fields | Tables / Columns | Notes (FKs) |
| --- | --- | --- | --- |
| ZIP metadata | `zip_metadata.*` | `ingest_sources.file_count`, `ingest_sources.total_uncompressed_bytes`, `ingest_sources.total_compressed_bytes` | `ingest_runs.source_id -> ingest_sources.id` |
| Project identity | `project_name`, `project_path`, `is_git_repo` | `projects.project_name`, `projects.project_key`, `project_runs.project_path`, `project_runs.is_git_repo` | `project_runs.project_id -> projects.id` |
| File inventory | `categorized_contents.*` | `files.relative_path`, `file_revisions.category`, `file_revisions.language` | `file_revisions.project_run_id -> project_runs.id` |
| File content hashes | `file_info[].sha256`, `file_info[].size` | `file_contents.content_hash`, `file_contents.size_bytes`, `file_revisions.content_id` | `file_revisions.content_id -> file_contents.id` |
| Code metrics | `analysis_results.code.metrics.*` | `project_metrics.total_files`, `project_metrics.total_lines`, `project_metrics.test_files` | `project_metrics.project_run_id -> project_runs.id` |
| Git metrics & duration | `git_analysis.*` | `project_metrics.total_commits`, `project_metrics.total_contributors`, `project_metrics.duration_*`, `project_metrics.activity_*` | `project_contributors.project_run_id -> project_runs.id` |
| Contributors | `git_analysis.contributors[]` | `project_contributors.name`, `project_contributors.email`, `project_contributors.commits` | FK to `project_runs` |
| Portfolio item core | `portfolio_item.tagline/description/project_type/complexity` | `portfolio_insights.*` | `portfolio_insights.project_run_id -> project_runs.id` |
| Portfolio key features | `portfolio_item.key_features[]` | `portfolio_key_features.feature_text`, `portfolio_key_features.display_order` | `portfolio_key_features.portfolio_insight_id -> portfolio_insights.id` |
| Resume bullets | `resume_item.bullets[]` | `resume_bullets.bullet_text`, `resume_bullets.display_order` | `resume_bullets.portfolio_insight_id -> portfolio_insights.id` |
| Languages/frameworks/skills | `project_metrics.languages/frameworks/skills` | `tags` + `project_tags` | `project_tags.project_run_id -> project_runs.id`, `tags.tag_type` distinguishes list type |
| Skill highlights | UI selection or overrides | `project_tags.is_highlighted`, `profile_project_tags.is_selected/display_order` | `profile_project_tags.profile_project_id -> profile_projects.id` |
| Skill evidence | `analysis_results.code.skill_analysis.evidence[]` | `skill_evidence.*` | `skill_evidence.file_revision_id -> file_revisions.id` |
| Keywords | `text_analyzer.top_keywords` | `tags` (tag_type=`keyword`) + `file_tags` or `project_tags` | `file_tags.file_revision_id -> file_revisions.id` |
| Text metrics | `text_analyzer.*` | `file_metric_values` (namespace=`text`) | `file_metric_values.file_revision_id -> file_revisions.id` |
| Image/video metrics | `image_analyzer` / `video_analyzer` | `file_metric_values` (namespace=`image`/`video`) | metrics stored as key/value rows |
| Ranking & summaries | `project_ranking.ranked_projects`, `project_ranking.top_summaries` | `ranking_runs`, `ranking_results`, `ranking_summaries` | `ranking_runs.run_id -> ingest_runs.id`, `ranking_results.project_run_id -> project_runs.id` |
| Chronological timeline | `chronological_skills.timeline[]` | `chronology_events`, `chronology_event_skills`, `chronology_event_metadata` | `chronology_events.run_id -> ingest_runs.id` |
| Chronology corrections | manual adjustments | `chronology_corrections.corrected_*` | `chronology_corrections.event_id -> chronology_events.id` |
| Thumbnails | image selection for UI | `thumbnails.*` | `thumbnails.project_run_id -> project_runs.id`, optional `file_revision_id` |
| Portfolio/resume ordering & overrides | user profile selections | `presentation_profiles`, `profile_projects`, `profile_resume_bullets`, `profile_project_tags` | supports selection, ordering, and overrides |
| Presentation controls | view settings, themes | `presentation_controls.control_key/control_value` | linked to `presentation_profiles` |

This schema keeps the pipeline output queryable without storing opaque blobs, while preserving a clear path for incremental ingestion, file dedupe, and per-profile presentation customization.
