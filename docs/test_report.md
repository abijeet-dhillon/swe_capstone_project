# Test Report

## 1. Purpose
- This report documents the repository's test suite for future developers, TAs, and reviewers.
- It explains what is tested, how tests are run, which strategies are used, and what limits/conditions apply.
- All statements are based on repository contents plus direct command runs in this workspace.

## 2. Test Environment
- Primary backend test path is Docker + `pytest` (documented in both `README.md` and `docs/installation_guide.md`).
- Frontend tests use Vitest + React Testing Library in `jsdom`.
- API smoke checks are also available via a shell script.

Recommended commands:

```bash
# Backend (full suite; canonical)
docker compose run --rm backend pytest -q

# Backend API-focused subset
docker compose run --rm backend pytest -q tests/api tests/insights tests/projects

# Backend local fallback (requires local Python deps)
pytest -q

# Frontend
cd frontend
npm test
# or
npm run test:watch

# API smoke script (backend must already be running on localhost:8000)
./test_filter_api.sh
```

Repo-grounded tooling/config used by tests:
- Backend: `pytest`, `pytest-asyncio`, `httpx`, FastAPI `TestClient`, SQLite temp DBs.
- Frontend: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`.
- Docker backend image includes system deps used by analyzers (for example `ffmpeg`, `tesseract`, `libzbar`, LaTeX tooling).

Observed command outcomes in this workspace:
- `docker compose run --rm backend pytest -q`: `740 passed, 3 skipped`.
- `docker compose run --rm backend pytest -q tests/api tests/insights tests/projects`: `189 passed`.
- `cd frontend && npm test`: `4 files passed`, `38 tests passed` (with React `act(...)` warnings).

## 3. Test Files Included in This Project

- `tests/api/` (12 files):
  - `test_health.py`, `test_runs.py`, `test_heatmap.py`, `test_linkedin_endpoints.py`, `test_portfolio_site_generation.py`, `test_privacy_consent.py`, `test_profile_endpoints.py`, `test_projects_endpoints.py`, `test_projects_upload_representation.py`, `test_resume_and_skills_endpoints.py`, `test_skills_endpoints.py`, `test_top_projects.py`.
  - Validates HTTP endpoint behavior, status codes, payload schemas, validation errors, role/profile/privacy flows, resume/portfolio generation routes, and project upload/representation behavior.

- `tests/projects/`:
  - `test_thumbnail_upload.py`.
  - Validates thumbnail form rendering, MIME/size validation, and upload success/error paths.

- `tests/insights/` (8 files):
  - `test_comparison.py`, `test_deletion.py`, `test_example_retrieval.py`, `test_file_analysis_cache.py`, `test_insights_store.py`, `test_portfolio_customization.py`, `test_project_filter.py`, `test_skill_trends.py`.
  - Validates persistent storage, schema migration behavior, encrypted file-analysis cache behavior, filtering/presets, deletion semantics, comparison summaries, and skills trend retrieval.

- `tests/pipeline/` (11 files):
  - `test_git_identifier.py`, `test_json_report.py`, `test_list_filtering.py`, `test_llm_consent_flow.py`, `test_orchestrator.py`, `test_orchestrator_coverage.py`, `test_orchestrator_presentation_integration.py`, `test_pipeline_cli.py`, `test_presentation_demo.py`, `test_presentation_pipeline.py`, `test_progress_tracker.py`.
  - Validates pipeline orchestration, JSON report artifacts, CLI command routing, consent flow logic, listing/filtering behavior, presentation generation paths, and progress/cancellation tracking.

- `tests/project/`:
  - `test_aggregator.py`, `test_presentation.py`, `test_top_summary.py`.
  - Validates project metrics aggregation/ranking and portfolio/resume item generation logic.

- `tests/resume/`:
  - `test_resume_artifact.py`.
  - Validates resume LaTeX context/rendering/escaping and PDF artifact generation error/success behavior.

- `tests/roles/`:
  - `test_presentation_roles.py`, `test_user_role_store.py`.
  - Validates user-role persistence and role propagation into presentation outputs.

- `tests/analyze/` (6 files):
  - `test_chronological_skills.py`, `test_code_analyzer.py`, `test_lang_frameworks.py`, `test_success_metrics.py`, `test_text_analyzer.py`, `test_video_analyzer.py`.
  - Validates language/framework detection, code/text/video analysis behavior, chronological skill timeline building, and success metric scoring.

- `tests/git/`:
  - `test_git_backend_fallback.py`, `test_git_project_analyzer.py`.
  - Validates git backend abstraction/fallback logic and repository analytics output.

- `tests/consent/`:
  - `test_directory_consent.py`, `test_llm_consent.py`.
  - Validates consent state lifecycle, timestamps, backward compatibility methods, and self-healing config behavior.

- `tests/config/`:
  - `test_config_manager.py`.
  - Validates SQLite-backed user config persistence and CLI prompt/update flows.

- `tests/data/`:
  - `test_database.py`.
  - Validates basic DB creation/read/cleanup behavior.

- `tests/ingest/`:
  - `test_zip_parser.py`.
  - Validates ZIP parsing, invalid/corrupt handling, and categorized parse structure.

- `tests/categorize/`:
  - `test_file_categorizer.py`.
  - Validates flattened file categorization output and language grouping.

- `tests/integrations/`:
  - `test_linkedin_formatter.py`.
  - Validates LinkedIn formatter output variations (hashtags/emojis/truncation/edge cases).

- Root-level backend tests in `tests/`:
  - `test_advanced_skill_extractor.py`, `test_cancellation.py`, `test_environment.py`, `test_git_individual_analyzer.py`, `test_image_processor.py`, `test_llm_analyzer.py`, `test_resume_customization.py`.
  - Covers advanced skill extraction patterns, cancellation lifecycle, environment smoke check, individual git contribution analytics, image processing logic, LLM analyzer logic (mostly mocked), and resume customization rules.

- Frontend tests:
  - `frontend/tests/App.test.tsx`, `frontend/tests/ProfileView.test.tsx`, `frontend/src/renderer/src/api.test.ts`, `frontend/src/renderer/src/components/SkillsTimeline.test.tsx`.
  - Covers app layout/navigation/theme behavior, profile load/save flows, API wrapper request construction, and timeline interactions/mutation flows.

- Non-standard script-like files relevant to testing context:
  - `tests/test_enhanced_processor.py` (interactive script-style tool; not a normal pytest test module).
  - `src/test_repository_analysis.py` and `src/test_summarization.py` (script/integration-helper style under `src/`; see limitations section).

## 4. Test Strategies Used

- Unit tests:
  - Pure function/class validation for analyzers, formatters, ranking logic, resume customization, metrics/dataclasses, and helper utilities.
  - Confidence: core computation and transformation logic is checked without external services.

- HTTP/API tests without a live server process:
  - FastAPI `TestClient` and `httpx` `ASGITransport`/`AsyncClient` exercise router behavior in-process.
  - Confidence: endpoint contracts, status codes, payload validation, and dependency wiring are verified.

- Integration-style persistence tests (SQLite):
  - Tests create temporary DBs, run real insert/update/read/delete flows, and verify persisted readback.
  - Confidence: storage schema and data lifecycle behavior are validated beyond isolated units.

- Fixture/factory-driven tests:
  - Heavy use of `tmp_path`, `tempfile`, custom fixtures, and `tests/insights/utils.py` synthetic payloads.
  - Confidence: repeatable test setup across many modules with realistic structured inputs.

- ZIP/sample-artifact driven tests:
  - Tests construct ZIPs dynamically and also use sample ZIP fixtures under `tests/`.
  - Confidence: ingest and categorization logic is validated on archive-style inputs used by pipeline flows.

- Git integration tests using temporary repositories:
  - Tests create throwaway git repos via subprocess, commit data, and validate analytics output/fallbacks.
  - Confidence: git analytics behavior is exercised against real commit history data.

- Mocking/stubbing of heavy or optional dependencies:
  - Multiple pipeline tests stub video/image/ML-heavy modules and monkeypatch external interactions.
  - Confidence: orchestrator and consent/control-flow logic remain testable even when optional heavy stacks are absent.

- Error-path and validation tests:
  - Tests explicitly check invalid payloads, missing files, bad ZIPs, unsupported formats, and API validation failures.
  - Confidence: defensive behavior and failure handling are covered, not just happy paths.

- Frontend component + interaction tests:
  - Vitest + RTL tests validate render state, user interactions, async loading/error behavior, and API call wiring.
  - Confidence: major renderer/UI flows are exercised in `jsdom` without full E2E browser automation.

- Concurrency/thread-safety checks:
  - Progress/cancellation and tracker registry tests include concurrent access scenarios.
  - Confidence: selected shared-state paths are checked for race-prone behavior.

## 5. Test Data and Fixtures
- `tests/conftest.py` ensures repo root is on import path for test execution.
- `tests/insights/utils.py` provides shared synthetic pipeline payload generation used across API/insights/presentation tests.
- Temporary SQLite fixtures are common across backend suites (`tmp_path`/`tempfile`) to avoid mutating project DB state.
- ZIP and sample artifacts used by tests/docs include:
  - `tests/test-zips/*.zip`
  - `tests/categorize/demo_projects.zip`
  - `tests/categorize/demo_projects_2.zip`
  - `tests/pipeline/example.zip`
  - `tests/pipeline/demo_capstone_project.zip`
  - `tests/demo_capstone_project.zip`
- Structured sample project trees under `tests/categorize/demo_projects/` and `tests/categorize/demo_projects2/` support categorization/ingest scenarios.
- Several tests generate temporary git repositories and commits to validate analytics logic.
- API tests frequently override FastAPI dependencies (`app.dependency_overrides`) to inject test stores/config managers.
- Frontend tests mock API modules to isolate UI behavior from backend availability.

## 6. Known Limitations / Conditions
- Docker is the reliable backend path in this repo. In this workspace, non-Docker `pytest --collect-only` failed during import with missing local dependencies (for example `fastapi`, `cv2`, `reportlab`, `pptx`).
- Full Docker backend run still has 3 expected skips:
  - `src/test_summarization.py` (explicitly skipped; integration helper requiring external API/file path).
  - `tests/test_llm_analyzer.py::TestIntegration::test_real_api_call` (requires `OPENAI_API_KEY`).
  - `tests/git/test_git_backend_fallback.py::test_gitpython_backend_available` (skipped if GitPython unavailable in runtime image).
- `tests/test_enhanced_processor.py` is interactive/script-style and is not part of normal assert-based pytest coverage.
- `src/test_repository_analysis.py` and `src/test_summarization.py` are helper scripts in `src/`; they are not core unit/API suites and are environment-dependent.
- Frontend tests pass but currently emit React `act(...)` warnings in `App.test.tsx` flows.
- `test_filter_api.sh` is a manual smoke script, not a pytest/vitest suite; it requires a running backend on `localhost:8000`.

## 7. Recommended Workflow for Future Developers
1. Run backend tests with Docker from repo root:

```bash
docker compose run --rm backend pytest -q
```

2. During API/storage work, run the faster subset:

```bash
docker compose run --rm backend pytest -q tests/api tests/insights tests/projects
```

3. Run frontend tests before merging UI or API-client changes:

```bash
cd frontend
npm test
```

4. If changing LLM-integrated code, set `OPENAI_API_KEY` and run relevant integration tests intentionally.
5. Optionally run API smoke script after starting backend (`docker compose up -d backend`) to sanity-check filter endpoints:

```bash
./test_filter_api.sh
```

## 8. Summary
- The suite combines unit, API, integration/persistence, fixture-driven, and frontend interaction tests.
- Backend coverage is broad across ingestion, analysis, storage, API routes, pipeline orchestration, presentation output, and consent/config flows.
- Frontend coverage targets key renderer interactions and API wrapper behavior.
- Practical confidence is highest when tests are run through the documented Docker workflow, with clear handling of the few conditional/integration skips.
