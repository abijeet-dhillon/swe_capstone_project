# Installation Guide

## 1. Purpose

This guide is for future developers onboarding to the **Digital Work Artifact Miner** repository. It documents how to install dependencies, configure environment settings, initialize storage, run backend/frontend components, run tests, and debug common local setup issues.

## 2. Repository Overview

Major components in this repository:

- `src/`: Python backend and pipeline logic.
- `src/api/`: FastAPI app and routers.
- `src/pipeline/`: ZIP analysis pipeline orchestration and CLI.
- `frontend/`: Electron + React desktop frontend (Vite + Vitest).
- `portfolio-template/`: Next.js portfolio site template used by portfolio generation features.
- `tests/`: Python test suite and sample ZIP fixtures.
- `docs/`: project documentation.
- `scripts/`: helper scripts for Docker-based local workflows.
- `data/`: SQLite database location (`data/app.db`).
- `uploads/`: uploaded ZIP staging directory (mounted to container as `/uploads`).
- `reports/`: generated report outputs.

Dependency/config files:

- Backend: `requirements.txt` (root), `Dockerfile`, `docker-compose.yml`.
- Additional/legacy Python deps list: `src/requirements.txt`.
- Frontend: `frontend/package.json`, `frontend/package-lock.json`.
- Portfolio template: `portfolio-template/package.json`, `portfolio-template/package-lock.json`.
- Environment templates: `env.template`, `src/env.example`.

## 3. Prerequisites

Required (recommended path):

- Git
- Docker Desktop / Docker Engine with Compose support

Required for non-Docker local development:

- Python (repo contains mixed indicators: Docker image is `python:3.10-slim`)
- Node.js + npm (version is not pinned in repo)

Optional:

- OpenAI API key (`OPENAI_API_KEY`) for LLM-backed features
- `sqlite3` CLI for database inspection

## 4. Required Tools

- Python + `venv` tooling (for non-Docker backend runs)
- npm (for `frontend/` and `portfolio-template/`)
- Docker + Docker Compose (recommended backend runtime)
- SQLite (embedded DB; no separate DB server required)
- Optional host tools used by scripts: `curl`, `lsof`

## 5. Developmental Setup
**Note: This inital setup is for development purpose, to run the whole application as a user would see it (docker, frontend, portfolio), see section [Running the Application Locally](#running-the-application-locally).

### Option A (Recommended): Docker backend + local frontend tooling

```bash
git clone <your-repo-url>
cd capstone-project-team-14

cp env.template .env
docker compose build backend
docker compose up -d backend
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ../portfolio-template
npm install
cd ..
```

### Option B: Non-Docker backend (optional)

```bash
git clone <your-repo-url>
cd capstone-project-team-14

cp env.template .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell) venv activation:

```powershell
.venv\Scripts\Activate.ps1
```

## 6. Environment Configuration

Create `.env` at repo root:

```bash
cp env.template .env
```

Environment variables observed in code/docs:

- `OPENAI_API_KEY`: used by OpenAI client code (`src/llm/openai_client.py`, `src/services/*`, `src/llm_analyzer.py`).
- `DATABASE_URL`: backend DB path override; defaults to `sqlite:///data/app.db`.
- `PIPELINE_USER_ID`: default user id for pipeline CLI consent/config storage.
- `INSIGHTS_ENCRYPTION_KEY`: serializer key in insights storage (legacy encrypted blob compatibility).
- `THUMBNAIL_STORAGE_ROOT`: thumbnail directory root (default `data/thumbnails`).
- `THUMBNAIL_MAX_BYTES`: max thumbnail upload size in bytes (default 5 MiB).
- `USE_REAL_OPENAI`: enables real OpenAI client in `src/llm_analyzer.py` (otherwise it uses an offline stub path).

Variables present in `env.template` but not directly referenced in runtime code paths scanned (`OPENAI_MODEL`, `OPENAI_TEMPERATURE`, `OPENAI_MAX_TOKENS`) are listed in Section 12 for confirmation.

Notes:

- `.env` is gitignored (`.gitignore` includes `.env`).
- Docker compose sets `DATABASE_URL=sqlite:///data/app.db` for the backend container.

## 7. Database Setup

Database technology: **SQLite**.

- Default DB file: `data/app.db`.
- No manual migration command is required.
- Schema initialization/migrations occur automatically in:
  - `ProjectInsightsStore` (`src/insights/storage.py`)
  - `UserConfigManager` (`src/config/config_manager.py`)

To initialize/populate data, run a pipeline analysis:

```bash
docker compose run --rm backend python -m src.pipeline.orchestrator tests/categorize/demo_projects.zip
```

Inspect DB contents (optional):

```bash
docker compose run --rm backend sqlite3 data/app.db
```

Seed/test ZIP data locations:

- `tests/categorize/demo_projects.zip`
- `tests/categorize/demo_projects_2.zip`
- `tests/test-zips/project_snapshot_early.zip`
- `tests/test-zips/project_snapshot_later.zip`
- `tests/test-zips/test-data.zip`

## 8. Running the Application Locally

### Full stack one-command launcher

Mac/Linux:

```bash
./start-miner.sh
```

Windows:

```bat
start-miner.bat
```

This script path starts:

- Docker backend API
- `portfolio-template` dev server
- Electron frontend app

### Backend only (Docker)

```bash
docker compose up -d backend
```

Backend URLs:

- API base: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Backend only (non-Docker)

Preferred local command (same as compose command):

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Alternative module launch:

```bash
python -m src.api.app
```

Note: `python -m src.api.app` uses port `8010` in `src/api/app.py`.

### Frontend (manual start order)

1. Start backend first (`localhost:8000`).
2. Start portfolio template (if you need site preview on `localhost:3000`):

```bash
cd portfolio-template
npm run dev
```

3. Start desktop frontend:

```bash
cd frontend
npm run dev
```

Alternative desktop start (build then run):

```bash
cd frontend
npm run start
```

## 9. Running Tests

### Backend tests (Python)

All backend tests (recommended via Docker):

```bash
docker compose run --rm backend pytest -q
```

API-focused subset from root README:

```bash
docker compose run --rm backend pytest -q tests/api tests/insights tests/projects
```

Local (non-Docker) backend test run:

```bash
pytest -q
```

### Frontend tests (Electron/React)

```bash
cd frontend
npm test
```

Watch mode:

```bash
cd frontend
npm run test:watch
```

### API smoke script

Requires backend running on `localhost:8000`:

```bash
./test_filter_api.sh
```

### Test prerequisites notes

- Some tests and flows use ZIP fixtures under `tests/`.
- LLM-dependent paths require `OPENAI_API_KEY`.

## 10. Recommended Developer Workflow

1. Clone repo and copy env template (`cp env.template .env`).
2. Build/start backend (`docker compose build backend && docker compose up -d backend`).
3. Install Node deps in `frontend/` and `portfolio-template/`.
4. Run one sample pipeline ZIP to initialize DB:

```bash
docker compose run --rm backend python -m src.pipeline.orchestrator tests/categorize/demo_projects.zip
```

5. Run frontend (or `./start-miner.sh` for integrated startup).
6. Run tests before commit:

```bash
docker compose run --rm backend pytest -q
cd frontend && npm test
```

## 11. Troubleshooting

- `POST /projects/upload` returns `404 Consent not found for user` or `403 Data access consent not granted`:
  register consent first using `POST /privacy-consent`.
- `ZIP file not found` errors:
  ensure `zip_path` is visible to the runtime context.
  For Docker-backed API, use repo-mounted paths like `tests/...` or `/uploads/...` (Electron upload flow copies files into `uploads/`).
- API unreachable on port 8000:
  check backend container status and port conflicts:

```bash
./scripts/check-ports.sh
./scripts/kill-port.sh 8000
```

- `python -m src.api.app` not available at `:8000`:
  that entrypoint binds to `:8010`.
- Frontend cannot fetch backend data:
  frontend API base is hardcoded to `http://localhost:8000` in `frontend/src/renderer/src/api.ts`; backend must be on that URL.
- Portfolio site generation endpoint says server not started:
  when backend runs in Docker, `POST /portfolio/generate-site` may skip starting Next.js dev server; run on host:

```bash
cd portfolio-template
npm run dev
```

- Non-Docker dependency errors (OCR/video/PDF/resume generation):
  host may be missing system packages included in Dockerfile (`ffmpeg`, `tesseract`, `libzbar`, LaTeX packages). Prefer Docker for consistent setup.
