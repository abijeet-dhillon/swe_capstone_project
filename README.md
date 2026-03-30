# Digital Work Artifact Miner

Team 14 - COSC 499 Capstone Project

Digital Work Artifact Miner is a privacy-first, local-first system that analyzes approved project artifacts (code, documents, and media), stores structured insights, and helps users generate resume and portfolio content. The platform supports both backend/API workflows and a desktop frontend, with optional OpenAI enhancement gated by explicit user consent.

## Milestone 3 Demo Video

**Watch the Milestone 3 demo:** [https://drive.google.com/file/d/1zg3qebNtaky_yXT5HaGNRyPbqaj-epZY/view?usp=sharing](https://drive.google.com/file/d/1zg3qebNtaky_yXT5HaGNRyPbqaj-epZY/view?usp=sharing)

## Overview

- Ingests project ZIPs and local artifacts through a controlled pipeline.
- Performs analysis locally by default (LLM features are optional).
- Persists project insights in SQLite for retrieval, comparison, and editing.
- Exposes FastAPI endpoints for upload, analysis, insights, resume, and portfolio workflows.
- Includes an Electron + React frontend and a Next.js portfolio template.

## Milestone 3 Status / Final Deliverables

The repository now includes a complete end-to-end workflow for Milestone 3:

- Backend pipeline and API service (`src/`, `src/api/`, `src/pipeline/`).
- Desktop frontend for user interaction (`frontend/`).
- Resume generation and editing flows (`/resume/*` endpoints).
- Portfolio generation and customization flows (`/portfolio/*` endpoints).
- Project insights features including skills extraction, timeline/chronology, filtering, comparison, and LinkedIn preview formatting.

## Repository Navigation

### Final Submission Documents For This Milestone

- [Installation Guide](docs/installation_guide.md)
- [Test Report](docs/test_report.md)
- [Known Bugs List](docs/known_bugs_list.md)
- [System Architecture Diagram](docs/plan/revised-uml-diagram.png)
- [DFD Level 0](docs/plan/uml_diagram.png)
- [DFD Level 1](docs/plan/level1dfd.png)

### Core References From Previous Milestones

- [Documentation Index](docs/DOCUMENTATION_INDEX.md)
- [API Reference](docs/api/API_REFERENCE.md)
- [Quick Commands](docs/QUICK_COMMANDS.md)
- [System Demo Walkthrough](docs/system_demo_walkthrough.md)
- [Test Results](docs/TEST_RESULTS.md)
- [Chronological Skills Guide](docs/CHRONOLOGICAL_SKILLS_GUIDE.md)
- [Team Contract](docs/plan/team14_team_contract.pdf)

## Quick Start

### Option A: Full Application (recommended for demos/grading)

1. Ensure Docker Desktop is running.
2. From repo root:

```bash
# Mac/Linux
./start-miner.sh
```

```bat
:: Windows
start-miner.bat
```

This launcher brings up:

- Docker backend API
- Portfolio template dev server
- Electron desktop frontend

### Option B: Backend/API Only (fast verification path)

```bash
cp env.template .env
docker compose build backend
docker compose up -d backend
```

Run pipeline on milestone datasets:

```bash
# Baseline snapshot
docker compose run --rm backend python -m src.pipeline.orchestrator tests/test-zips/project_snapshot_early.zip

# Later snapshot
docker compose run --rm backend python -m src.pipeline.orchestrator tests/test-zips/project_snapshot_later.zip

# Multi-project dataset
docker compose run --rm backend python -m src.pipeline.orchestrator tests/test-zips/test-data.zip
```

Open API docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development Setup

Use the full onboarding guide for future developers:

- [docs/installation_guide.md](docs/installation_guide.md)

Key repository areas:

- `src/` backend logic and API
- `frontend/` Electron + React client
- `portfolio-template/` generated portfolio site template
- `tests/` backend tests and fixtures
- `docs/` project documentation

## Running the Application

### Backend

```bash
docker compose up -d backend
```

### Frontend + Portfolio (manual)

```bash
cd portfolio-template
npm install
npm run dev
```

In another terminal:

```bash
cd frontend
npm install
npm run start
```

For active frontend development, use `npm run dev` in `frontend/`.

## Testing

Backend (full suite):

```bash
docker compose run --rm backend pytest -q
```

Backend API-focused subset:

```bash
docker compose run --rm backend pytest -q tests/api tests/insights tests/projects
```

Frontend tests:

```bash
cd frontend
npm test
```

API smoke script (backend must be running):

```bash
./test_filter_api.sh
```

Detailed testing evidence and outcomes:

- [docs/test_report.md](docs/test_report.md)
- [docs/TEST_RESULTS.md](docs/TEST_RESULTS.md)

## Core Features

- Privacy and consent flow before project upload (`/privacy-consent`, pipeline consent checks).
- ZIP ingestion and project extraction with local persistence.
- Skills extraction and chronology endpoints (`/skills`, `/chronological/*`).
- Resume generation and editing (`/resume/generate`, `/resume/{id}`, `/resume/{id}/edit`).
- Portfolio generation and editing (`/portfolio/generate`, `/portfolio/{id}`, `/portfolio/{id}/edit`).
- Project filtering, comparison, and recommendation endpoints (`/filter/*`, `/compare/*`).
- LinkedIn preview generation/customization (`/linkedin/preview/*`).
- Project role and thumbnail customization endpoints.
- Incremental update workflow (`/projects/update/{old_zip_hash}`).

## Milestone Verification and API Commands

Core endpoints to verify:

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

Additional milestone-relevant routes:

- Incremental update: `POST /projects/update/{old_zip_hash}`
- Role management: `PUT /projects/{id}/role`, `GET /projects/{id}/role`
- Thumbnail management: `POST|GET|DELETE /projects/{id}/thumbnail`
- Representation customization: `POST /projects/upload/{skills|ranking|chronology|attributes|showcase}`
- Filtering/comparison/LinkedIn/insights endpoints

<details>
<summary>Copy-paste API verification flow</summary>

```bash
# Start services
docker compose build backend
docker compose up -d backend
export API=http://localhost:8000

# Consent (required before upload)
curl -X POST "$API/privacy-consent" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "ta_user",
    "zip_path": "tests/test-zips/test-data.zip",
    "llm_consent": false,
    "data_access_consent": true
  }'

# Upload and analyze
curl -X POST "$API/projects/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "ta_user",
    "zip_path": "tests/test-zips/test-data.zip"
  }'

# Retrieve ids
curl "$API/projects"
curl "$API/runs"

# API tests
docker compose run --rm backend pytest -q tests/api tests/insights tests/projects
```

</details>

Full endpoint catalog:

- [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md)

## Architecture

### System Architecture Diagram

![System architecture diagram](docs/plan/revised-uml-diagram.png)

### DFD Level 0

![DFD Level 0](docs/plan/uml_diagram.png)

### DFD Level 1

![DFD Level 1](docs/plan/level1dfd.png)

## Documentation

- [Documentation Index](docs/DOCUMENTATION_INDEX.md)
- [Installation Guide](docs/installation_guide.md)
- [Test Report](docs/test_report.md)
- [Known Bugs List](docs/known_bugs_list.md)
- [API Reference](docs/api/API_REFERENCE.md)
- [System Demo Walkthrough](docs/system_demo_walkthrough.md)
- [LLM Setup Guide](docs/LLM_SETUP_GUIDE.md)
- [LLM Architecture](docs/LLM_ARCHITECTURE.md)
- [Database Process](docs/database_process.md)

## Known Issues

Known issue tracking for handoff and maintenance:

- [docs/known_bugs_list.md](docs/known_bugs_list.md)

## Team / Course Context

This repository is the Team 14 capstone submission for COSC 499. It is organized as a handoff-ready project with implementation, verification artifacts, and developer-facing documentation for future continuation.

## Work Breakdown Structure (WBS)

### Mining Digital Work Artifacts System

### Team 14: Privacy-First Portfolio Mining Pipeline

Short form summary of the original WBS:

1. **1.0 Project Management** - planning, team coordination, stakeholder communication.
2. **2.0 Requirements Analysis and Design** - requirements, architecture, database, security/privacy design.
3. **3.0 Scanner and Configuration Module** - config management, scanning, ZIP validation, file type detection.
4. **4.0 Adapter Framework** - Git/doc/media adapters and fallback adapter support.
5. **5.0 Data Processing Pipeline** - normalization, deduplication, redaction, storage.
6. **6.0 Analytics and Insights Engine** - local analytics, optional LLM integration, ranking and portfolio insights.
7. **7.0 API Development** - FastAPI setup, endpoint implementation, authorization and audit controls.
8. **8.0 Export and Reporting Module** - JSON/CSV/PDF export flows and report templates.
9. **9.0 Testing and Quality Assurance** - unit, integration, performance, security, and UAT coverage.
10. **10.0 Infrastructure and DevOps** - environment setup, CI/CD, containerization, monitoring/logging.
11. **11.0 Documentation** - technical, user, and developer documentation deliverables.
12. **12.0 Deployment and Release** - release prep, deployment execution, post-deployment validation.
13. **13.0 Project Closure** - final deliverables and knowledge transfer.

Supporting planning artifacts remain under `docs/plan/`, `docs/logs/`, and other `docs/` subfolders.
