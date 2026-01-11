# System Demo Walkthrough (≈10 minutes)

End-to-end checklist to demo the pipeline: install, run without LLM, run with LLM, retrieve both runs, and clean up. All commands are copy/paste ready from repo root.

## 0) Install & prerequisites

- Ensure Docker is running.
- Build and start backend once:
  ```bash
  docker compose build backend
  docker compose up -d backend
  ```
- Default DB path is `data/app.db`; schema migrations create the normalized `projects`, `files`, and `portfolio_insights` tables.
- Data access consent is prompted once per user/ZIP and stored (like LLM consent). If the user declines, the pipeline exits immediately with no output on subsequent runs too.

## 1) Consent + baseline run (no LLM)

This run satisfies: consent prompt, zip parsing, wrong-format guard, alternative (local-only) analysis, config storage, project/type detection, metrics, skills, ranking, timeline, DB persistence.

1. **Try wrong format (expect error)**

   ```bash
   docker compose run --rm backend python -m src.pipeline.orchestrator README.md
   ```

   - Confirms requirement #3 (non-zip rejected).
   - First prompt: **Data access consent** (answer once; stored).
   - When prompted for LLM consent, answer **n** (requirements #1, #4, #5).
   - User consent choice is stored in user config for reuse (#6).

2. **Run proper ZIP, decline LLM (local-only analysis)**

   ```bash
   docker compose run --rm backend python -m src.pipeline.orchestrator tests/categorize/demo_projects.zip
   ```

   - The run will: parse the ZIP (#2), separate projects (#7), detect languages/frameworks (#8), compute contributions (git) (#9), extract metrics (#10), extract skills (#11), output per-project info (#12), rank projects (#16), summarize top ranked (#17), build chronological projects/skills (#19, #20), and persist to DB (#13).

## 2) Second run with LLM enabled (stored consent for user `root`)

Pre-store LLM consent for user `root`, then run with that user so the prompt is skipped and consent is reused.

```bash
# Store consent = yes for user root (pointing at a different ZIP to get a new hash)
docker compose run --rm backend python -m src.config.config_manager --user-id root --update --zip-file tests/categorize/demo_project_2.zip --llm-consent yes

# Run pipeline using stored consent
docker compose run --rm backend python -m src.pipeline.orchestrator --user-id root tests/categorize/demo_projects_2.zip
```

- This uses stored consent (requirements #1, #4, #5) and updates the `root` collection with refreshed portfolio/resume items.

## 3) List stored collections and projects

```bash
docker compose run --rm -T backend python - <<'PY'
import sqlite3

db = "data/app.db"
with sqlite3.connect(db) as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT collection_id, COUNT(*) AS project_count, MAX(updated_at) AS updated_at "
        "FROM projects GROUP BY collection_id ORDER BY updated_at DESC LIMIT 20;"
    ).fetchall()
    for row in rows:
        print(f"{row['collection_id']}  projects={row['project_count']}  updated={row['updated_at']}")
PY
```

## 4) Retrieve non-LLM run

**Quick-grab commands (non-LLM run):**

- Portfolio only:

  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[-1]["collection_id"]
      project = conn.execute(
          "SELECT id, name FROM projects "
          "WHERE collection_id = ? AND name != '_misc_files' "
          "ORDER BY name LIMIT 1;",
          (collection_id,),
      ).fetchone()
      insights = conn.execute(
          "SELECT * FROM portfolio_insights "
          "WHERE project_id = ? AND presentation_type = 'portfolio';",
          (project["id"],),
      ).fetchone()
      print(json.dumps(dict(insights) if insights else {}, indent=2, sort_keys=True))
  PY
  ```

  - retrieve previously generated portfolio information (#14)

- Resume bullets only:

  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[-1]["collection_id"]
      project = conn.execute(
          "SELECT id FROM projects "
          "WHERE collection_id = ? AND name != '_misc_files' "
          "ORDER BY name LIMIT 1;",
          (collection_id,),
      ).fetchone()
      row = conn.execute(
          "SELECT resume_bullets_json FROM portfolio_insights "
          "WHERE project_id = ? AND presentation_type = 'resume';",
          (project["id"],),
      ).fetchone()
      bullets = json.loads(row["resume_bullets_json"]) if row and row["resume_bullets_json"] else []
      print(json.dumps(bullets, indent=2, sort_keys=True))
  PY
  ```

  - retrieve previously generated résumé item (#15)

- Advanced skills extraction + chronological timeline (global insights):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[-1]["collection_id"]
      rows = conn.execute(
          "SELECT name, start_date_raw, end_date_raw, start_date_override, "
          "end_date_override, skills_detected_json "
          "FROM projects WHERE collection_id = ? "
          "ORDER BY COALESCE(start_date_override, start_date_raw) ASC;",
          (collection_id,),
      ).fetchall()
      timeline = []
      for row in rows:
          skills = json.loads(row["skills_detected_json"]) if row["skills_detected_json"] else []
          timeline.append(
              {
                  "project": row["name"],
                  "skills": skills,
                  "start": row["start_date_override"] or row["start_date_raw"],
                  "end": row["end_date_override"] or row["end_date_raw"],
              }
          )
      print(json.dumps(timeline, indent=2, sort_keys=True))
  PY
  ```
- Project ranking & summaries (global insights):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[-1]["collection_id"]
      rows = conn.execute(
          "SELECT p.name, pi.display_order, pi.title_override, pi.summary_override, pi.display_text "
          "FROM projects p JOIN portfolio_insights pi ON pi.project_id = p.id "
          "WHERE p.collection_id = ? AND pi.presentation_type = 'portfolio' "
          "ORDER BY pi.display_order ASC, p.name ASC;",
          (collection_id,),
      ).fetchall()
      print(json.dumps([dict(row) for row in rows], indent=2, sort_keys=True))
  PY
  ```
- Whole analysis payload (everything stored for that project):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[-1]["collection_id"]
      project = conn.execute(
          "SELECT id, name FROM projects "
          "WHERE collection_id = ? AND name != '_misc_files' "
          "ORDER BY name LIMIT 1;",
          (collection_id,),
      ).fetchone()
      files = conn.execute(
          "SELECT * FROM files WHERE project_id = ? ORDER BY file_name;",
          (project["id"],),
      ).fetchall()
      insights = conn.execute(
          "SELECT * FROM portfolio_insights WHERE project_id = ? ORDER BY presentation_type;",
          (project["id"],),
      ).fetchall()
      payload = {
          "project": dict(project),
          "files": [dict(row) for row in files],
          "portfolio_insights": [dict(row) for row in insights],
      }
      print(json.dumps(payload, indent=2, sort_keys=True))
  PY
  ```

## 5) Retrieve LLM run

**Quick-grab commands (LLM run):**

- Portfolio only:
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[0]["collection_id"]
      project = conn.execute(
          "SELECT id, name FROM projects "
          "WHERE collection_id = ? AND name != '_misc_files' "
          "ORDER BY name LIMIT 1;",
          (collection_id,),
      ).fetchone()
      insights = conn.execute(
          "SELECT * FROM portfolio_insights "
          "WHERE project_id = ? AND presentation_type = 'portfolio';",
          (project["id"],),
      ).fetchone()
      print(json.dumps(dict(insights) if insights else {}, indent=2, sort_keys=True))
  PY
  ```
- Resume bullets only:
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[0]["collection_id"]
      project = conn.execute(
          "SELECT id FROM projects "
          "WHERE collection_id = ? AND name != '_misc_files' "
          "ORDER BY name LIMIT 1;",
          (collection_id,),
      ).fetchone()
      row = conn.execute(
          "SELECT resume_bullets_json FROM portfolio_insights "
          "WHERE project_id = ? AND presentation_type = 'resume';",
          (project["id"],),
      ).fetchone()
      bullets = json.loads(row["resume_bullets_json"]) if row and row["resume_bullets_json"] else []
      print(json.dumps(bullets, indent=2, sort_keys=True))
  PY
  ```
- Advanced skills extraction + chronological timeline (global insights):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[0]["collection_id"]
      rows = conn.execute(
          "SELECT name, start_date_raw, end_date_raw, start_date_override, "
          "end_date_override, skills_detected_json "
          "FROM projects WHERE collection_id = ? "
          "ORDER BY COALESCE(start_date_override, start_date_raw) ASC;",
          (collection_id,),
      ).fetchall()
      timeline = []
      for row in rows:
          skills = json.loads(row["skills_detected_json"]) if row["skills_detected_json"] else []
          timeline.append(
              {
                  "project": row["name"],
                  "skills": skills,
                  "start": row["start_date_override"] or row["start_date_raw"],
                  "end": row["end_date_override"] or row["end_date_raw"],
              }
          )
      print(json.dumps(timeline, indent=2, sort_keys=True))
  PY
  ```
- Project ranking & summaries (global insights):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[0]["collection_id"]
      rows = conn.execute(
          "SELECT p.name, pi.display_order, pi.title_override, pi.summary_override, pi.display_text "
          "FROM projects p JOIN portfolio_insights pi ON pi.project_id = p.id "
          "WHERE p.collection_id = ? AND pi.presentation_type = 'portfolio' "
          "ORDER BY pi.display_order ASC, p.name ASC;",
          (collection_id,),
      ).fetchall()
      print(json.dumps([dict(row) for row in rows], indent=2, sort_keys=True))
  PY
  ```
- Whole analysis payload (everything stored for that project):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import json
  import sqlite3

  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.row_factory = sqlite3.Row
      collections = conn.execute(
          "SELECT collection_id, MAX(updated_at) AS updated_at "
          "FROM projects GROUP BY collection_id ORDER BY updated_at DESC;"
      ).fetchall()
      if not collections:
          raise SystemExit("No projects found.")
      collection_id = collections[0]["collection_id"]
      project = conn.execute(
          "SELECT id, name FROM projects "
          "WHERE collection_id = ? AND name != '_misc_files' "
          "ORDER BY name LIMIT 1;",
          (collection_id,),
      ).fetchone()
      files = conn.execute(
          "SELECT * FROM files WHERE project_id = ? ORDER BY file_name;",
          (project["id"],),
      ).fetchall()
      insights = conn.execute(
          "SELECT * FROM portfolio_insights WHERE project_id = ? ORDER BY presentation_type;",
          (project["id"],),
      ).fetchall()
      payload = {
          "project": dict(project),
          "files": [dict(row) for row in files],
          "portfolio_insights": [dict(row) for row in insights],
      }
      print(json.dumps(payload, indent=2, sort_keys=True))
  PY
  ```

## 6) Retrieve via example CLI (full report, normalized read)

```bash
docker compose run --rm backend python -m src.insights.example_retrieval --db-path data/app.db
```

- Shows per-project outputs (#12), ranking (#16), top summaries (#17), timelines (#19, #20).
- Portfolio/resume items are read from `portfolio_insights` rows in the normalized schema.
- For a more readable, report-like view in the terminal, pipe through `less`:
  ```bash
  docker compose run --rm backend python -m src.insights.example_retrieval --db-path data/app.db | less -R
  ```
  (`-R` preserves simple formatting/indentation; use `q` to quit the pager.)

## 7) Delete insights safely

Choose either per-collection or all. Deleting a collection removes its projects, files, and portfolio insights; other collections remain.

- **Delete one collection by collection_id** (replace `<PUT_COLLECTION_ID_HERE>` with a value from section 3's command):
  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import sqlite3
  db = "data/app.db"
  target = "<PUT_COLLECTION_ID_HERE>"
  with sqlite3.connect(db) as conn:
      conn.execute("PRAGMA foreign_keys=ON;")
      result = conn.execute("DELETE FROM projects WHERE collection_id = ?;", (target,))
      conn.commit()
      print("Deleted projects:", result.rowcount)
  PY
  ```
- **Delete all insights**:

  ```bash
  docker compose run --rm -T backend python - <<'PY'
  import sqlite3
  db = "data/app.db"
  with sqlite3.connect(db) as conn:
      conn.execute("PRAGMA foreign_keys=ON;")
      result = conn.execute("DELETE FROM projects;")
      conn.commit()
      print("Deleted projects:", result.rowcount)
  PY
  ```

- **Delete all user configs**:
  ```bash
  docker compose run --rm -T backend python -c "import sqlite3,sys; db='data/app.db';
  conn=sqlite3.connect(db); conn.execute(\"DELETE FROM user_configurations\"); conn.commit();
  print('Deleted rows:', conn.execute('select changes()').fetchone()[0])"
  ```

## 8) Run all tests

```
docker compose run --rm backend pytest -q
```

## 9) Quick notes for the recording

- Total time should stay under 10 minutes if you follow the order above.
- Call out that data access consent is prompted every run and is not persisted; saying **n** stops the pipeline immediately.
- Highlight prompts for consent (LLM) and the fallback local analysis when declined.
- Show the wrong-format error step to prove validation.
- Point out collaborative vs individual (git contributor counts) and language/framework detection in pipeline output.
- Mention that portfolio and resume items, metrics, rankings, timelines, and skills are persisted and can be retrieved later.
