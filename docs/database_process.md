# Database Persistence Walkthrough (Dummy Data)

This document explains what would happen if you run:

```
docker compose run --rm backend python -m src.pipeline.orchestrator tests/categorize/demo_projects.zip
```

It is based on the current codepaths in `src/pipeline/orchestrator.py`, `src/insights/storage.py`, and `src/config/config_manager.py`. It does not execute the command.

## Would it save properly?

Yes, the data should persist because:

- The container mounts the repo to `/code` and mounts a named volume `sqlite_data` to `/code/data` (`docker-compose.yml`).
- SQLite writes to `/code/data/app.db` (via `DATABASE_URL=sqlite:///data/app.db` and `ProjectInsightsStore` default).
- The named volume survives container removal (`--rm` only removes the container).
- The JSON report is saved under `/code/reports`, which maps to your repo’s `./reports` directory.

You would only lose persisted data if you delete the `sqlite_data` volume or remove `data/app.db` on the host.

## Viewing tables after a run

Docker (same database file mounted into the container):

```
docker compose run --rm backend sqlite3 data/app.db
```

Inside the SQLite shell:

```
.tables
.schema
```

## Step-by-step: what gets saved and where

1. **Consent is resolved (user configuration)**

   - `resolve_data_access_consent()` and `resolve_llm_consent()` use `UserConfigManager`.
   - A row is created or updated in `user_configurations` (SQLite table in the same `data/app.db`).

2. **ZIP metadata is parsed**

   - `parse_zip()` calculates file counts and sizes.
   - The metadata becomes `zip_metadata` in the pipeline payload.

3. **Projects are identified and analyzed**

   - Top-level directories under `demo_projects/` become individual projects.
   - Files are categorized (code/docs/images/etc.) and analyzed.

4. **Insights DB is initialized**

   - `ProjectInsightsStore()` creates the schema if missing (migrations v1-v4).
   - This creates all normalized tables, plus legacy tables for compatibility.

5. **Normalized insight rows are written**

   - `record_pipeline_run()` writes to the normalized tables.
   - This includes ingest sources/runs, projects, project runs, files, file revisions, metrics, tags, portfolio/resume data, ranking, and chronology.

6. **Report JSON is written**
   - A report file is saved to `reports/report_YYYYMMDD_HHMMSS.json`.

## Tables created and populated on this run (dummy examples)

Below are representative rows showing how values map into each table. Field names match the schema; values are illustrative.

### user_configurations

Used for consent tracking and last zip path.

```
user_id: "abijeet"
zip_file: "tests/categorize/demo_projects.zip"
llm_consent: 0
llm_consent_asked: 1
data_access_consent: 1
created_at: "2026-01-07T17:46:07+00:00"
updated_at: "2026-01-07T17:46:12+00:00"
```

### schema_migrations

Applied on first run to build the schema.

```
version: 4
applied_at: "2026-01-07T17:46:10+00:00"
```

### ingest_sources

One row per unique ZIP (hash = filename + zip metadata).

```
id: 1
source_type: "zip"
source_path: "tests/categorize/demo_projects.zip"
source_name: "demo_projects"
source_hash: "b3a0b6c3...a1f9"  # 64 hex chars
file_count: 120
total_uncompressed_bytes: 201234
total_compressed_bytes: 45321
created_at: "2026-01-07T17:46:12+00:00"
updated_at: "2026-01-07T17:46:12+00:00"
```

### ingest_runs

One row per pipeline execution.

```
id: 1
source_id: 1
run_type: "full"
parent_run_id: null
pipeline_version: "artifact-pipeline/v1"
status: "completed"
started_at: "2026-01-07T17:46:12+00:00"
finished_at: "2026-01-07T17:46:20+00:00"
```

### projects

One row per project folder found under the ZIP root.

```
id: 1
source_id: 1
project_key: "project-mobile"
project_name: "project-mobile"
slug: "project-mobile"
root_path: "demo_projects/project-mobile"
created_at: "2026-01-07T17:46:13+00:00"
updated_at: "2026-01-07T17:46:13+00:00"
```

```
id: 2
source_id: 1
project_key: "project-webapp"
project_name: "project-webapp"
slug: "project-webapp"
root_path: "demo_projects/project-webapp"
created_at: "2026-01-07T17:46:13+00:00"
updated_at: "2026-01-07T17:46:13+00:00"
```

### project_runs

One row per project per pipeline run.

```
id: 1
project_id: 1
run_id: 1
project_path: "/tmp/unzipped_xxx/demo_projects/project-mobile"
is_git_repo: 0
created_at: "2026-01-07T17:46:14+00:00"
updated_at: "2026-01-07T17:46:14+00:00"
```

### files

Unique files per project (path is relative to project root).

```
id: 10
project_id: 1
relative_path: "ios/AppDelegate.swift"
file_name: "AppDelegate.swift"
extension: ".swift"
created_at: "2026-01-07T17:46:14+00:00"
```

### file_contents

De-duplicated by file content hash (if file_info includes sha256).

```
id: 33
content_hash: "c58d3f...f2b0"
size_bytes: 624
mime_type: null
created_at: "2026-01-07T17:46:14+00:00"
```

### file_revisions

Per run record of file metadata and categorization.

```
id: 120
file_id: 10
project_run_id: 1
content_id: 33
size_bytes: 624
modified_at: "2025-11-02T21:49:00+00:00"
is_binary: 0
is_deleted: 0
language: "Swift"
category: "code"
```

### file_metric_values

Analyzer outputs stored as key/value metrics (JSON or numeric).

```
id: 501
file_revision_id: 120
metric_namespace: "code"
metric_key: "analysis_json"
metric_value_text: "{\"file_path\":\".../AppDelegate.swift\",\"lines_of_code\":42,...}"
metric_value_num: null
metric_unit: null
```

```
id: 502
file_revision_id: 120
metric_namespace: "code"
metric_key: "lines_of_code"
metric_value_text: null
metric_value_num: 42
metric_unit: null
```

### tags

Shared tag catalog across projects/files.

```
id: 1
tag_type: "language"
name: "Swift"
category: null
```

```
id: 2
tag_type: "framework"
name: "React"
category: null
```

### project_tags

Project-level tags (languages/frameworks/skills/keywords).

```
project_run_id: 1
tag_id: 1
source: "local"
score: null
display_order: 0
is_highlighted: 0
```

### file_tags

File-level tags derived from per-file analysis.

```
file_revision_id: 120
tag_id: 1
score: null
```

### skill_evidence

Evidence for skills extracted from code analysis.

```
id: 77
project_run_id: 1
file_revision_id: 120
tag_id: 3
evidence_type: "import"
location: "AppDelegate.swift:1"
reasoning: "Imports UIKit"
confidence: null
```

### project_metrics

Aggregate metrics per project run.

```
project_run_id: 1
total_files: 18
total_lines: 840
total_commits: 0
total_contributors: 0
activity_code: 0
activity_test: 0
activity_doc: 0
duration_start: null
duration_end: null
duration_days: 0
doc_files: 2
doc_words: 340
image_files: 4
video_files: 0
test_files: 0
has_documentation: 1
has_tests: 0
has_images: 1
has_videos: 0
```

### project_contributors

Only populated when git analysis finds contributors.

```
id: 1
project_run_id: 2
name: "Jane Doe"
email: "jane@example.com"
commits: 12
```

### portfolio_insights / portfolio_key_features / resume_bullets

Generated portfolio/resume outputs (from `generate_portfolio_item()` and `generate_resume_item()`).

```
portfolio_insights:
  id: 1
  project_run_id: 2
  generated_at: "2026-01-07T17:46:18+00:00"
  pipeline_version: "artifact-pipeline/v1"
  tagline: "Mobile tracker app"
  description: "Offline-first tracker with sync support."
  project_type: "mobile app"
  complexity: "medium"
  is_collaborative: 0
  summary: "Built a Swift-based mobile app with shared UI components."
```

```
portfolio_key_features:
  portfolio_insight_id: 1
  feature_text: "Syncs local data with background jobs"
  display_order: 0
```

```
resume_bullets:
  portfolio_insight_id: 1
  bullet_text: "Developed an offline-first mobile app with sync and caching."
  display_order: 0
  is_selected: 1
  source: "generated"
```

### ranking_runs / ranking_results / ranking_summaries

Project ranking is stored if `project_ranking` is present in the payload.

```
ranking_runs:
  id: 1
  run_id: 1
  criteria: "score"
  created_at: "2026-01-07T17:46:19+00:00"
```

```
ranking_results:
  ranking_run_id: 1
  project_run_id: 2
  rank: 1
  score: 0.92
  recency_days: 14
  commits: 12
  loc: 1400
  duration_days: 30
```

```
ranking_summaries:
  ranking_run_id: 1
  project_run_id: 2
  summary: "Highest activity and strongest documentation coverage."
```

### chronology_events / chronology_event_skills / chronology_event_metadata

Chronological skill timeline (if generated) is stored here.

```
chronology_events:
  id: 1
  run_id: 1
  file_revision_id: 120
  event_timestamp: "2025-10-20T12:00:00+00:00"
  category: "frontend"
```

```
chronology_event_skills:
  event_id: 1
  tag_id: 1  # Swift
```

```
chronology_event_metadata:
  id: 1
  event_id: 1
  metric_key: "lines_of_code"
  metric_value_text: null
  metric_value_num: 42
```

## Tables created but not written by this command

These are created by migrations but are not populated by the pipeline run above:

- `zipfile`, `project` (legacy encrypted tables)
- `deletion_audit` (only used by delete APIs)
- `chronology_corrections` (manual timeline edits)
- `thumbnails` (presentation assets)
- `presentation_profiles`, `profile_projects`, `profile_resume_bullets`, `profile_project_tags`, `presentation_controls`

## Where to look after a real run

- SQLite DB: `data/app.db`
- JSON report: `reports/report_YYYYMMDD_HHMMSS.json`
- DB schema reference: `docs/design/database_schema.md`
