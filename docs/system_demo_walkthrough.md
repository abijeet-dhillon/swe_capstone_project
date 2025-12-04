# System Demo Walkthrough (≈10 minutes)

End-to-end checklist to demo the pipeline: install, run without LLM, run with LLM, retrieve both runs, and clean up. All commands are copy/paste ready from repo root.

## 0) Install & prerequisites

- Ensure Docker is running.
- Build and start backend once:
  ```bash
  docker compose build backend
  docker compose up -d backend
  ```
- Default DB path is `data/app.db`; encryption uses the fixed local key unless you override `INSIGHTS_ENCRYPTION_KEY`.
- Data access consent is prompted once per user/ZIP and stored (like LLM consent). If the user declines, the pipeline exits immediately with no output on subsequent runs too.

## 1) Consent + baseline run (no LLM)

This run satisfies: consent prompt, zip parsing, wrong-format guard, alternative (local-only) analysis, config storage, project/type detection, metrics, skills, ranking, timeline, DB persistence.

1. **Try wrong format (expect error)**

   ```bash
   docker compose run --rm backend python -m src.pipeline.orchestrator README.md
   ```

   Confirms requirement #3 (non-zip rejected).

2. **Run proper ZIP, decline LLM (local-only analysis)**
   ```bash
   docker compose run --rm backend python -m src.pipeline.orchestrator tests/categorize/demo_projects.zip
   ```
   - First prompt: **Data access consent** (answer once; stored).
   - When prompted for LLM consent, answer **n** (requirements #1, #4, #5).
   - The run will: parse the ZIP (#2), separate projects (#7), detect languages/frameworks (#8), compute contributions (git) (#9), extract metrics (#10), extract skills (#11), output per-project info (#12), rank projects (#16), summarize top ranked (#17), build chronological projects/skills (#19, #20), and persist to DB (#13). User consent choice is stored in user config for reuse (#6).

## 2) Second run with LLM enabled (stored consent for user `root`)

Pre-store LLM consent for user `root`, then run with that user so the prompt is skipped and consent is reused.

```bash
# Store consent = yes for user root (pointing at a different ZIP to get a new hash)
docker compose run --rm backend python -m src.config.config_manager --user-id root --update --zip-file tests/categorize/demo_project_2.zip --llm-consent yes

# Run pipeline using stored consent
docker compose run --rm backend python -m src.pipeline.orchestrator --user-id root tests/categorize/demo_project_2.zip
```

- This uses stored consent (requirements #1, #4, #5) and persists a second set of insights (different `zip_hash` unless contents unchanged) including portfolio/resume items.

## 3) List stored runs (zip hashes and project names)

```bash
docker compose run --rm -T backend python - <<'PY'
from src.insights.storage import ProjectInsightsStore
store = ProjectInsightsStore(db_path="data/app.db")
runs = store.list_recent_zipfiles(limit=5)
for r in runs:
    print("zip_hash:", r["zip_hash"], "projects:", r["total_projects"])
    print("  names:", store.list_projects_for_zip(r["zip_hash"]))
PY
```

## 4) Retrieve non-LLM run (portfolio + resume items)

```bash
docker compose run --rm -T backend python - <<'PY'
from src.insights.storage import ProjectInsightsStore

store = ProjectInsightsStore(db_path="data/app.db")
zh = store.list_recent_zipfiles(limit=2)[-1]["zip_hash"]  # older run (assume non-LLM)
projects = [p for p in store.list_projects_for_zip(zh) if p != "_misc_files"]
if not projects:
    print("No non-misc projects found.")
else:
    name = projects[0]
    payload = store.load_project_insight(zh, name)
    print("Project:", name)
    print("Keys:", sorted(payload.keys()))
    print("Portfolio:", payload.get("portfolio_item"))
    print("Resume bullets:", payload.get("resume_item", {}).get("bullets", []))
    print("Ranking info:", payload.get("project_ranking"))
    print("Timeline:", payload.get("chronological_skills", {}).get("timeline", [])[:2])
PY
```

**Quick-grab commands (LLM run):**

- Analysis payload (project-level):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  import json
  s = ProjectInsightsStore(db_path="data/app.db")
  zh = s.list_recent_zipfiles(limit=1)[0]["zip_hash"]
  proj = [p for p in s.list_projects_for_zip(zh) if p != "_misc_files"][0]
  payload = s.load_project_insight(zh, proj)
  print(json.dumps(payload, indent=2, sort_keys=True))
  PY
  ```
- Portfolio only:
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  import json
  s = ProjectInsightsStore(db_path="data/app.db")
  zh = s.list_recent_zipfiles(limit=1)[0]["zip_hash"]
  proj = [p for p in s.list_projects_for_zip(zh) if p != "_misc_files"][0]
  payload = s.load_project_insight(zh, proj)
  print(json.dumps(payload.get("portfolio_item"), indent=2, sort_keys=True))
  PY
  ```
- Resume bullets only:
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  import json
  s = ProjectInsightsStore(db_path="data/app.db")
  zh = s.list_recent_zipfiles(limit=1)[0]["zip_hash"]
  proj = [p for p in s.list_projects_for_zip(zh) if p != "_misc_files"][0]
  payload = s.load_project_insight(zh, proj)
  print(json.dumps(payload.get("resume_item", {}).get("bullets", []), indent=2, sort_keys=True))
  PY
  ```

## 5) Retrieve LLM run (same fields)

````bash
docker compose run --rm -T backend python - <<'PY'
from src.insights.storage import ProjectInsightsStore

store = ProjectInsightsStore(db_path="data/app.db")
zh = store.list_recent_zipfiles(limit=2)[-1]["zip_hash"]  # older run (assume non-LLM)
projects = [p for p in store.list_projects_for_zip(zh) if p != "_misc_files"]
if not projects:
    print("No non-misc projects found.")
else:
    name = projects[0]
    payload = store.load_project_insight(zh, name)
    print("Project:", name)
    print("Keys:", sorted(payload.keys()))
    print("Portfolio:", payload.get("portfolio_item"))
    print("Resume bullets:", payload.get("resume_item", {}).get("bullets", []))
    print("Ranking info:", payload.get("project_ranking"))
    print("Timeline:", payload.get("chronological_skills", {}).get("timeline", [])[:2])
PY

**Quick-grab commands (non-LLM run):**

- Analysis payload (project-level):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  import json
  s = ProjectInsightsStore(db_path="data/app.db")
  zh = s.list_recent_zipfiles(limit=2)[-1]["zip_hash"]
  proj = [p for p in s.list_projects_for_zip(zh) if p != "_misc_files"][0]
  payload = s.load_project_insight(zh, proj)
  print(json.dumps(payload, indent=2, sort_keys=True))
  PY
````

- Portfolio only:
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  import json
  s = ProjectInsightsStore(db_path="data/app.db")
  zh = s.list_recent_zipfiles(limit=2)[-1]["zip_hash"]
  proj = [p for p in s.list_projects_for_zip(zh) if p != "_misc_files"][0]
  payload = s.load_project_insight(zh, proj)
  print(json.dumps(payload.get("portfolio_item"), indent=2, sort_keys=True))
  PY
  ```
- Resume bullets only:
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  import json
  s = ProjectInsightsStore(db_path="data/app.db")
  zh = s.list_recent_zipfiles(limit=2)[-1]["zip_hash"]
  proj = [p for p in s.list_projects_for_zip(zh) if p != "_misc_files"][0]
  payload = s.load_project_insight(zh, proj)
  print(json.dumps(payload.get("resume_item", {}).get("bullets", []), indent=2, sort_keys=True))
  PY
  ```

**Quick-grab commands (LLM run):**

- Analysis payload (project-level):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  import json
  s = ProjectInsightsStore(db_path="data/app.db")
  zh = s.list_recent_zipfiles(limit=1)[0]["zip_hash"]
  proj = [p for p in s.list_projects_for_zip(zh) if p != "_misc_files"][0]
  payload = s.load_project_insight(zh, proj)
  print(json.dumps(payload, indent=2, sort_keys=True))
  PY
  ```
- Portfolio only:
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  import json
  s = ProjectInsightsStore(db_path="data/app.db")
  zh = s.list_recent_zipfiles(limit=1)[0]["zip_hash"]
  proj = [p for p in s.list_projects_for_zip(zh) if p != "_misc_files"][0]
  payload = s.load_project_insight(zh, proj)
  print(json.dumps(payload.get("portfolio_item"), indent=2, sort_keys=True))
  PY
  ```
- Resume bullets only:
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  import json
  s = ProjectInsightsStore(db_path="data/app.db")
  zh = s.list_recent_zipfiles(limit=1)[0]["zip_hash"]
  proj = [p for p in s.list_projects_for_zip(zh) if p != "_misc_files"][0]
  payload = s.load_project_insight(zh, proj)
  print(json.dumps(payload.get("resume_item", {}).get("bullets", []), indent=2, sort_keys=True))
  PY
  ```

## 6) Retrieve via example CLI (full report, encrypted read)

```bash
docker compose run --rm backend python -m src.insights.example_retrieval --db-path data/app.db
```

- Shows per-project outputs (#12), ranking (#16), top summaries (#17), timelines (#19, #20).
- Portfolio/resume items are embedded in the decrypted payload.

## 7) Delete insights safely

Choose either per-zip or all. Deleting a zip only removes that run; other runs remain (requirement #18 about not affecting shared files across reports).

- **Delete one run by zip_hash** (replace `<hash>`):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  store = ProjectInsightsStore(db_path="data/app.db")
  target = store.list_recent_zipfiles(limit=1)[0]["zip_hash"]
  print("Deleting zip_hash:", target)
  print(store.delete_zip(target))
  PY
  ```
- **Delete everything**:
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  from src.insights.storage import ProjectInsightsStore
  store = ProjectInsightsStore(db_path="data/app.db")
  print(store.delete_all())
  PY
  ```

## 8) Quick notes for the recording

- Total time should stay under 10 minutes if you follow the order above.
- Call out that data access consent is prompted every run and is not persisted; saying **n** stops the pipeline immediately.
- Highlight prompts for consent (LLM) and the fallback local analysis when declined.
- Show the wrong-format error step to prove validation.
- Point out collaborative vs individual (git contributor counts) and language/framework detection in pipeline output.
- Mention that portfolio and resume items, metrics, rankings, timelines, and skills are persisted and can be retrieved later.
