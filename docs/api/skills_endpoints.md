# Skills Endpoints Walkthrough (API + Tests)
This document explains the files `src/api/routers/skills.py` and `tests/api/test_skills_endpoints.py`, while also showing how to demo the new skills endpoints end-to-end with Docker.
## 1) What `src/api/routers/skills.py` does
The skills router supports:
- aggregate read: `GET /skills`
- per-project reads/mutations: `GET /skills/{project_id}`, `POST /skills/add`, `POST /skills/edit`, `POST /skills/remove`
- timeline filter: `GET /skills/year?year=YYYY`
### Request models
- `SkillsAddPayload`: `{ "project_id": int, "skills": [str, ...] }`
- `SkillsRemovePayload`: `{ "project_id": int, "skills": [str, ...] }`
- `SkillsEditPayload`:
  - replace one skill: `{ "project_id": int, "old": str, "new": str }`
  - replace whole list: `{ "project_id": int, "skills": [str, ...] }`
  - if `skills` exists, full replacement is used.
### Internal helpers
- `_normalize_skills(values)`: trims whitespace, drops empty values, normalizes with `.casefold()` (stored lowercase), dedupes while preserving first occurrence order.
- `_load_project_skills_or_404(project_id, store)`: calls `store.load_project_insight_by_id(project_id)`, raises `404` if project does not exist, reads `project_metrics.skills`, normalizes.
- `_skills_response(project_id, skills)`: returns `{ "project_id": <id>, "skills": [ ... ] }`.
### Endpoint behavior details
- `POST /skills/add`: appends incoming skills to existing project list, normalizes + dedupes, persists through `store.update_project_skills(...)`.
- `POST /skills/remove`: normalizes removal candidates, removes case-insensitively, persists updated list.
- `POST /skills/edit`: if `skills` is provided, replaces full list; otherwise requires `old` + `new`; if `old` not found returns no-op `200`; then replaces and persists.
- `GET /skills/{project_id}`: returns persisted per-project skill list (normalized).
- `GET /skills/year?year=YYYY`: validates year via FastAPI query constraints (`1000..9999`), loads latest global insights, filters `global_insights["chronological_skills"]["timeline"]` by year prefix in `timestamp`, returns `{ "year": YYYY, "timeline": [...] }`, and returns empty timeline with `200` when no global timeline exists.
### Persistence used by router
The router relies on two new store methods in `src/insights/storage.py`:
- `update_project_skills(project_id: int, skills: list[str]) -> None`: updates `project_info.skills_json`, updates `updated_at`, commits transaction.
- `load_latest_global_insights() -> dict | None`: selects latest row from `ingest`, reuses `_load_global_insights(...)`, returns `None` when no insights exist.
No schema changes and no new tables were introduced.
## 2) What `tests/api/test_skills_endpoints.py` validates
The test file uses a temporary SQLite DB and dependency override pattern:
- seeds one project through `record_pipeline_run(...)`
- seeds chronological timeline data at top level (`chronological_skills`) with mixed years
- overrides `deps.get_store` to isolate tests
- uses FastAPI `TestClient`
Covered test cases:
1. add endpoint normalizes and dedupes
2. remove endpoint is case-insensitive
3. edit endpoint: old -> new replace works; old missing returns no-op `200`
4. edit full replacement with `skills` list
5. get by project id returns expected list
6. year endpoint filters timeline correctly
7. unknown project id returns `404`
8. invalid year fails with validation (`422`)
## 3) Demo walkthrough (Docker)
## 0) Build and start container
```bash
docker compose build backend
docker compose up -d backend
```
## 1) Seed DB with a pipeline run (creates project rows + chronology)
```bash
docker compose run --rm backend python -m src.pipeline.orchestrator demo_capstone_project.zip
```
If prompted for LLM consent, choose either option; skills endpoints work in both modes.
## 2) Start FastAPI server on port 8000
Option A:
```bash
./scripts/start-api.sh
```
Option B:
```bash
docker compose run --rm -p 8000:8000 backend python -m src.api.app
```
API docs: `http://localhost:8000/docs`
### NOTE: Run all commands below this in a second terminal
## 3) Basic health check
```bash
curl http://localhost:8000/health
```
Expected:
```json
{ "status": "ok" }
```
## 4) Find a valid `project_id`
```bash
docker compose run --rm -T backend python - <<'PY'
from src.insights.storage import ProjectInsightsStore
from src.pipeline.presentation_pipeline import PresentationPipeline

store = ProjectInsightsStore(db_path="data/app.db")
projects = PresentationPipeline(insights_store=store).list_available_projects()
for p in projects:
    print(p["project_id"], p["project_name"], p["zip_hash"])
PY
```
Pick one `project_id` from output and export it:
```bash
export PROJECT_ID=<PUT_PROJECT_ID_HERE>
```
View the skills for the selected project id:
```bash
curl http://localhost:8000/skills/$PROJECT_ID
```
## 5) Exercise all skills endpoints
### 5.1 Add
```bash
curl -X POST http://localhost:8000/skills/add \
  -H "Content-Type: application/json" \
  -d '{"project_id": '"$PROJECT_ID"', "skills": [" Python ", "python", "FASTAPI", ""]}'
```
Expected shape:
```json
{ "project_id": 123, "skills": ["python", "fastapi"] }
```
### 5.2 Edit (single replace)
```bash
curl -X POST http://localhost:8000/skills/edit \
  -H "Content-Type: application/json" \
  -d '{"project_id": '"$PROJECT_ID"', "old": "fastapi", "new": "backend"}'
```
### 5.3 Edit (full replacement)
```bash
curl -X POST http://localhost:8000/skills/edit \
  -H "Content-Type: application/json" \
  -d '{"project_id": '"$PROJECT_ID"', "skills": ["graphql", "API", "graphql"]}'
```
### 5.4 Remove
```bash
curl -X POST http://localhost:8000/skills/remove \
  -H "Content-Type: application/json" \
  -d '{"project_id": '"$PROJECT_ID"', "skills": ["API"]}'
```
### 5.5 Get project skills
```bash
curl http://localhost:8000/skills/$PROJECT_ID
```
### 5.6 Year filter
```bash
curl "http://localhost:8000/skills/year?year=2026"
```
### 5.7 404 demo
```bash
curl http://localhost:8000/skills/999999
```
### 5.8 Validation demo (422)
```bash
curl "http://localhost:8000/skills/year?year=26"
```
## 6) Run endpoint tests in Docker
```bash
docker compose run --rm backend pytest -q tests/api/test_skills_endpoints.py
```
Optional: run legacy API test that also touches skills aggregation:
```bash
docker compose run --rm backend pytest -q tests/api/test_resume_and_skills_endpoints.py
```
## 7) Stop/cleanup
If you started server with `start-api.sh` or `docker compose run`, stop with `Ctrl+C`.
Then stop background container:
```bash
docker compose down
```
