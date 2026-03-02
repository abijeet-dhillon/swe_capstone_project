# API Reference

Comprehensive reference for the FastAPI service in this repository.

## Service Overview

- Framework: FastAPI
- Main app: `src/api/app.py`
- Interactive docs: `/docs` (Swagger UI), `/redoc`
- Health route: `GET /health`
- Runs route: `GET /runs`

### Ports

- `docker-compose.yml` runs API on port `8000`.
- Running `python -m src.api.app` directly uses port `8010` in `src/api/app.py`'s `__main__` block.

## Milestone Core Endpoints

These are the milestone-required endpoints (or direct equivalents):

- `POST /projects/upload`
- `POST /privacy-consent`
- `GET /projects`
- `GET /projects/{id}`
- `GET /skills`
- `GET /resume/{id}`
- `POST /resume/generate`
- `POST /resume/{id}/edit`
- `GET /portfolio/{id}`
- `POST /portfolio/generate`
- `POST /portfolio/{id}/edit`

## Common Behavior

- Content type:
  - JSON for most routes (`application/json`)
  - multipart form-data for thumbnail upload routes
- Typical errors:
  - `400` invalid input
  - `403` missing consent
  - `404` not found
  - `422` schema validation error
  - `500` internal pipeline/storage error

## Endpoint Groups

### System

#### `GET /health`

Health check.

Example response:
```json
{"status":"ok"}
```

#### `GET /runs`

Lists recent stored ZIP analysis runs.

Response: array of run metadata (`zip_hash`, `zip_path`, timestamps, project counts, etc.).

### Privacy and Consent

#### `POST /privacy-consent`

Stores/updates user consent and active zip path.

Request body:
```json
{
  "user_id": "alice",
  "zip_path": "tests/test-zips/test-data.zip",
  "llm_consent": false,
  "data_access_consent": true
}
```

Response:
```json
{
  "status": "ok",
  "user_id": "alice",
  "zip_path": "tests/test-zips/test-data.zip",
  "llm_consent": false,
  "data_access_consent": true
}
```

#### `POST /git-identifier`

Stores the user git identifier used in pipeline analysis.

Request:
```json
{"user_id":"alice","git_identifier":"alice@example.com"}
```

#### `GET /git-identifier/{user_id}`

Gets stored git identifier for a user.

### Projects

#### `POST /projects/upload`

Runs pipeline for a user-provided zip and returns represented output.

Request body:
```json
{
  "user_id": "alice",
  "zip_path": "tests/test-zips/test-data.zip",
  "representation": {
    "sections": ["projects", "ranking", "skills", "showcase"],
    "ranking": {"criteria":"score","n":3},
    "skills": {"highlight":["python"],"suppress":[]},
    "showcase": {"selected_projects":["ProjectAlpha"]}
  }
}
```

Response includes:

- `status`
- `zip_hash`
- `ingest_id`
- `projects` (project names)
- `representation` (resolved config)
- `represented_output` (selected view sections)

#### `POST /projects/upload/{section}`

Section-scoped upload wrappers:

- `POST /projects/upload/skills`
- `POST /projects/upload/ranking`
- `POST /projects/upload/chronology`
- `POST /projects/upload/attributes`
- `POST /projects/upload/showcase`

Same request body as `/projects/upload`. Response includes only that represented section.

#### `GET /projects`

Lists available projects.

Returns `project_id`, `project_name`, `zip_hash`, git/code/doc counts, timestamps.

#### `GET /projects/{project_id}`

Full stored project payload by ID. Includes project insight data, plus:

- merged `user_role` (if set)
- thumbnail references (if present)

#### `PUT /projects/{project_id}/role`

Sets the user role for a project.

Request:
```json
{"role":"Lead Developer"}
```

Response:
```json
{"project_id":123,"user_role":"Lead Developer"}
```

#### `GET /projects/{project_id}/role`

Gets user role for a project.

#### `POST /projects/{project_id}/thumbnail`

Uploads project thumbnail image.

- multipart field: `file`
- allowed MIME: `image/png`, `image/jpeg`, `image/jpg`, `image/webp`
- max bytes from env `THUMBNAIL_MAX_BYTES` (default 5MB)

Response includes `thumbnail_path`, `thumbnail_url`, `mime_type`, `size_bytes`.

#### `GET /projects/{project_id}/thumbnail`

Returns stored thumbnail metadata.

#### `GET /projects/{project_id}/thumbnail/content`

Returns actual image content.

#### `DELETE /projects/{project_id}/thumbnail`

Deletes thumbnail association and file.

#### `POST /projects/update/{old_zip_hash}`

Incremental update endpoint.

Request body:
```json
{
  "user_id":"alice",
  "old_zip_hash":"<hash>",
  "new_zip_path":"tests/test-zips/project_snapshot_later.zip"
}
```

Response keys:

- `status`
- `old_zip_hash`
- `new_zip_hash`
- `new_only_projects`
- `retained_projects`
- `updated_projects`
- `total_projects`

### Portfolio

#### `GET /portfolio/templates`

Lists portfolio templates (`industry`, `academic`) and usage.

#### `GET /portfolio/templates/{template_id}`

Returns template details for `industry` or `academic`.

#### `GET /portfolio/{project_id}`

Returns portfolio showcase payload.

Optional query:

- `template=industry|academic`

Response includes base fields:

- `project_id`, `project_title`, `user_role`
- `description`, `summary`
- `key_skills`, `key_metrics`
- optional `thumbnail_path`, `thumbnail_url`
- optional `success_metrics`

Template mode adds template-specific sections and fields.

#### `POST /portfolio/generate`

Regenerates and persists portfolio item.

Query parameter:

- `project_id` (int)

#### `POST /portfolio/{project_id}/edit`

Persists portfolio customizations.

Request body (all optional):
```json
{
  "tagline": "High-impact backend system",
  "description": "Built a scalable API...",
  "project_type": "backend",
  "complexity": "complex",
  "is_collaborative": true,
  "summary": "Delivered measurable improvements",
  "key_features": ["Feature A", "Feature B"]
}
```

### Resume

#### `GET /resume/{project_id}`

Returns resume item for a project, plus merged `user_role` if available.

#### `POST /resume/generate`

Regenerates and persists resume bullets.

Query parameter:

- `project_id` (int)

#### `POST /resume/{project_id}/edit`

Persists custom resume bullets.

Request:
```json
{
  "bullets": [
    "Led backend API design",
    "Improved reliability and test coverage"
  ]
}
```

### Skills

#### `GET /skills`

Returns aggregate unique skill list across projects.

#### `GET /skills/year?year=YYYY`

Returns timeline entries filtered by year from latest global chronological skills.

#### `GET /skills/{project_id}`

Returns normalized per-project skills.

#### `POST /skills/add`

Request:
```json
{"project_id":123,"skills":["Python","FastAPI"]}
```

#### `POST /skills/remove`

Request:
```json
{"project_id":123,"skills":["fastapi"]}
```

#### `POST /skills/edit`

Two modes:

- replace specific skill:
```json
{"project_id":123,"old":"fastapi","new":"backend"}
```
- replace full list:
```json
{"project_id":123,"skills":["graphql","api"]}
```

### Chronological

#### `GET /chronological/skills`

Query params:

- `zip_hash` (optional; defaults to most recent run)
- `project_name` (optional; defaults to first non-`_misc_files` project)

Returns chronological skills timeline for one project.

#### `GET /chronological/skills/{project_id}`

Project-ID variant of chronological skills timeline.

#### `GET /chronological/projects`

Query param:

- `limit` (default 50)

Returns chronological project list across recent runs.

### Comparison

Prefix: `/compare`

#### `GET /compare/projects`

Compares all available projects and returns synthesized comparison insights.

Optional query:

- `user_id`

#### `POST /compare/projects/{project_id_1}/vs/{project_id_2}`

Compares two projects.

#### `POST /compare/match-job`

Matches projects to a job description.

Request:
```json
{
  "job_description": "Backend engineer with API and Python experience",
  "top_n": 3
}
```

#### `GET /compare/growth`

Returns growth trajectory/timeline derived from projects.

#### `GET /compare/recommendations`

Returns recommendation set from comparison engine.

### LinkedIn

Prefix: `/linkedin`

#### `GET /linkedin/preview/{project_id}`

Query params:

- `include_hashtags` (bool, default true)
- `include_emojis` (bool, default true)

Returns formatted LinkedIn post preview:

- `text`, `char_count`, `exceeds_limit`, `hashtags`, `preview`

#### `POST /linkedin/preview/{project_id}/custom`

Body-controlled formatting:
```json
{"include_hashtags":true,"include_emojis":false}
```

### Filtering

Prefix: `/filter`

#### `POST /filter/`

Applies advanced project filtering.

Request model `ProjectFilterRequest`:

- `date_range`: `{ "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }`
- `languages`: string[]
- `frameworks`: string[]
- `skills`: string[]
- `project_type`: `individual | collaborative | all`
- `complexity`: string
- `metrics`: `min/max lines, commits, contributors, files`
- `search_text`: string
- `sort_by`:  
  `importance | date_desc | date_asc | loc_desc | loc_asc | commits_desc | commits_asc | name_asc | name_desc | contributors_desc | contributors_asc`
- `limit`: int (1..1000)
- `offset`: int (>=0)

Response:

- `total`
- `projects`
- `filter_applied`

#### Presets

- `GET /filter/presets`
- `GET /filter/presets/{preset_id}`
- `POST /filter/presets`
- `DELETE /filter/presets/{preset_id}`
- `POST /filter/presets/{preset_id}/apply`

Save preset request:
```json
{
  "name":"Backend-heavy projects",
  "description":"Projects with strong backend profile",
  "filter_config":{
    "languages":["python"],
    "project_type":"all",
    "sort_by":"importance"
  }
}
```

#### Search and metadata

- `GET /filter/search?q=<term>&limit=50`
- `GET /filter/options`
- `GET /filter/skills/trends?skill=<skill>`
- `GET /filter/skills/progression`

### Insights (Data Management and Customization)

Prefix: `/insights`

#### Data deletion

- `DELETE /insights/` (delete all insights)
- `DELETE /insights/zips/{zip_hash}`
- `DELETE /insights/projects/{zip_hash}/{project_name}`

#### Cancellation

- `POST /insights/cancel/{zip_hash}`

Cancels active analysis (if tracked) and schedules cleanup.

#### Portfolio customization patch

- `PATCH /insights/portfolio/{project_info_id}`

Request:
```json
{
  "portfolio_fields": {
    "tagline": "Updated tagline",
    "description": "Updated description",
    "key_features": ["A", "B"],
    "is_collaborative": true
  },
  "resume_bullets": ["Bullet 1", "Bullet 2"]
}
```

Allowed `portfolio_fields` keys:

- `tagline`
- `description`
- `project_type`
- `complexity`
- `is_collaborative`
- `summary`
- `key_features`

### Insights Role Routes (zip_hash + project_name)

Also under `/insights`:

- `GET /insights/projects/{zip_hash}/{project_name}`
- `PUT /insights/projects/{zip_hash}/{project_name}/role`

Set role request:
```json
{"user_role":"Lead Developer"}
```

### Legacy Project Thumbnail Routes

Defined in `src/projects/api.py` (also under `/projects`):

- `GET /projects/{project_name}/thumbnail` (HTML upload form)
- `POST /projects/{project_name}/thumbnail` (lightweight upload validation echo)

These are separate from the ID-based thumbnail persistence routes in `src/api/routers/projects.py`.

## Notes for Clients

- For new integrations, prefer ID-based project routes from `src/api/routers/projects.py`.
- For complete machine-readable schema, rely on generated OpenAPI at `/openapi.json`.
