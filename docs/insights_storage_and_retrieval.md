# Insights Storage & Retrieval Guide

This guide explains how to persist pipeline insights into the local SQLite database and how to retrieve those stored results later. It assumes you have already pulled the repository, created the Python virtual environment, and can run the existing pipeline orchestrator.

---

## 1. Prerequisites

- **Encryption key**: Insights are stored in encrypted blobs. Provide `INSIGHTS_ENCRYPTION_KEY` before running the pipeline. For development, the store falls back to a local placeholder, but production data should always use a strong secret.
- **Database location**: By default, data is stored in `data/app.db`. When running under Docker Compose, the backend service mounts a named volume (`sqlite_data`) at `/code/data`, so the DB file lives inside that volume.
- **Docker Compose**: The recommended flow uses `docker-compose` to ensure consistent dependencies. All commands below run from the repository root.

---

## 2. Storing Insights via the Pipeline Orchestrator

1. **Generate an encryption key (optional but recommended)**:

   ```bash
   python - <<'PY'
   import secrets
   print(secrets.token_hex(32))
   PY
   ```

2. **Run the pipeline with environment variables passed to the container**:

   ```bash
   docker-compose run --rm \
     -e INSIGHTS_ENCRYPTION_KEY=<your-hex-key> \
     -e DATABASE_URL=sqlite:///data/app.db \
     backend \
     python -m src.pipeline.orchestrator tests/categorize/demo_projects.zip
   ```

   - Replace `<your-hex-key>` with the string generated in step 1.
   - Swap the ZIP path with your own archive as needed.
   - The run prints the usual six pipeline steps, and near the end you should see:

     ```
     [5b/6] Persisting insights to database...
          ✓ Stored insights (... inserted / ... updated / ... deleted)
     ```

   - The database now contains encrypted rows in the `zipfile` and `project` tables (see `docs/design/database_schema.md` for schema details).

---

## 3. Inspecting the SQLite Database

To confirm rows were written, open a container shell that mounts the database volume and run `sqlite3`:

```bash
docker-compose run --rm backend sqlite3 data/app.db '.tables'
```

Expect to see `zipfile`, `project`, and `schema_migrations`. Note that the encrypted columns render as unreadable blobs; use the retrieval script to decrypt them.

---

## 4. Retrieving Stored Insights

Use the helper CLI `src/insights/example_retrieval.py` to print the same report the pipeline produced, but without re-running analysis.

### Basic usage

```bash
docker-compose run --rm \
  -e INSIGHTS_ENCRYPTION_KEY=<your-hex-key> \
  backend \
  python -m src.insights.example_retrieval --db-path data/app.db
```

Notes:

- If no `--zip-hash` is provided, the script fetches the most recently updated entry.
- Provide `--zip-hash <hash>` to retrieve a specific run (hash values come from `zipfile.zip_hash`).
- Use `--db-path` if you stored the database somewhere other than the default `data/app.db`.

### Sample output

```
======================================================================
Retrieval From Database
======================================================================

ZIP Summary:
   - Total files: 60
   - Uncompressed size: 18.00 KB
   - Compressed size: 3.81 KB

Projects Found: 2
Miscellaneous Files: Yes (2 loose files)

... (full project summaries and detailed analysis follow)
```

The script reconstructs both the high-level summary (projects, file counts, analyses) and the detailed per-project sections you see during a live pipeline run, but without any Unicode emojis so logs stay ASCII-friendly.

### Full Testing Workflow (from repo root)

1. **Build and start the backend container**

   ```bash
   docker compose build backend
   docker compose up -d backend
   ```

2. **Run the pipeline to persist insights** (using the demo ZIP; swap for your own)

   ```bash
   docker compose run --rm \
     -e INSIGHTS_ENCRYPTION_KEY=<your-hex-key> \
     -e DATABASE_URL=sqlite:///data/app.db \
     backend \
     python -m src.pipeline.orchestrator tests/categorize/demo_projects.zip
   ```

3. **Inspect the database via sqlite3**

   ```bash
   docker compose run --rm backend sqlite3 data/app.db
   ```

   Inside the `sqlite>` prompt you can verify or explore:

   ```
   .tables
   SELECT zip_hash, total_projects FROM zipfile;
   .quit
   ```

4. **Retrieve stored insights from the DB**

   ```bash
   docker compose run --rm \
     -e INSIGHTS_ENCRYPTION_KEY=<your-hex-key> \
     backend \
     python -m src.insights.example_retrieval --db-path data/app.db
   ```

   Use `--zip-hash <hash>` if you want to target a specific stored run.

5. **Run the insights pytest suite**
   ```bash
   docker compose run --rm backend pytest tests/insights -q
   docker compose run --rm backend pytest tests/insights -q --cov=src/insights --cov-report=term-
   ```

These steps cover the entire flow (store, inspect, retrieve, regressions) and ensure coverage stays above 80% for the new modules.

---

## 5. Backup and Restore

`ProjectInsightsStore` also exposes `backup()` and `restore()` methods:

- **Backup**: Copies the current DB file to a timestamped path.
- **Restore**: Replaces the active DB with the backup and reapplies migrations.

For ad hoc operations, you can run a small Python snippet inside the backend container:

```bash
docker-compose run --rm backend python - <<'PY'
from src.insights.storage import ProjectInsightsStore

store = ProjectInsightsStore(db_path="data/app.db")
backup_path = store.backup("data/backups/insights_backup.db")
print("Backup written to", backup_path)
PY
```

To restore:

```bash
docker-compose run --rm backend python - <<'PY'
from src.insights.storage import ProjectInsightsStore

store = ProjectInsightsStore(db_path="data/app.db")
store.restore("data/backups/insights_backup.db")
print("Restore complete")
PY
```

Ensure you keep the backup files outside the container volume if you need them across environments.

---

## 6. Summary

1. Run the pipeline with `docker-compose run --rm backend python -m src.pipeline.orchestrator <zip>` while passing `INSIGHTS_ENCRYPTION_KEY`.
2. The orchestrator automatically persists results in the `zipfile`/`project` tables.
3. Use `python -m src.insights.example_retrieval` (inside the backend container) to decrypt and print the stored insights, optionally specifying a `--zip-hash`.
4. Back up or restore the database using the provided helper methods when needed.

Following these steps keeps project insights encrypted, queryable, and easy to share without re-running lengthy analyses.
