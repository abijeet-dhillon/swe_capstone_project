"""
storage.py
----------
SQLite-backed persistence layer for storing encrypted insights coming out of the
pipeline orchestrator output.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import threading
import zlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_DB_URL = "sqlite:///data/app.db"
DEFAULT_DB_PATH = DEFAULT_DB_URL.replace("sqlite:///", "")
# Fixed local encryption key (overridable via INSIGHTS_ENCRYPTION_KEY env var)
DEFAULT_INSIGHTS_KEY = os.getenv("INSIGHTS_ENCRYPTION_KEY", "local-insights-key")
ZIP_TABLE = "zipfile"
PROJECT_TABLE = "project"
SCHEMA_VERSION = 2


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_parent(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def _canonical_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _iso_to_datetime(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


class SecureSerializer:
    """Compresses and encrypts insights before storing them in SQLite."""

    def __init__(self, key: Optional[bytes]) -> None:
        if key is None:
            env_key = DEFAULT_INSIGHTS_KEY
            key = env_key.encode("utf-8") if isinstance(env_key, str) else env_key
        if isinstance(key, str):  # pragma: no cover - defensive
            key = key.encode("utf-8")
        self._root_key = hashlib.sha256(key).digest()

    def _derive_stream(self, iv: bytes, length: int) -> bytes:
        """Derive a pseudo-random keystream using HMAC-SHA256."""
        stream = bytearray()
        counter = 0
        while len(stream) < length:
            counter_bytes = counter.to_bytes(4, "big")
            block = hmac.new(self._root_key, iv + counter_bytes, hashlib.sha256).digest()
            stream.extend(block)
            counter += 1
        return bytes(stream[:length])

    def encrypt(self, payload: Dict[str, Any]) -> bytes:
        serialized = _canonical_dumps(payload).encode("utf-8")
        compressed = zlib.compress(serialized, level=9)
        iv = os.urandom(16)
        keystream = self._derive_stream(iv, len(compressed))
        ciphertext = bytes(a ^ b for a, b in zip(compressed, keystream))
        mac = hmac.new(self._root_key, iv + ciphertext, hashlib.sha256).digest()
        return iv + ciphertext + mac

    def decrypt(self, blob: bytes) -> Dict[str, Any]:
        if len(blob) <= 48:
            raise ValueError("Ciphertext is too short to decrypt.")
        iv = blob[:16]
        mac = blob[-32:]
        ciphertext = blob[16:-32]
        expected_mac = hmac.new(self._root_key, iv + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("Ciphertext failed integrity verification.")
        keystream = self._derive_stream(iv, len(ciphertext))
        compressed = bytes(a ^ b for a, b in zip(ciphertext, keystream))
        decompressed = zlib.decompress(compressed)
        return json.loads(decompressed.decode("utf-8"))


class PayloadValidationError(ValueError):
    """Raised when the pipeline output does not meet schema requirements."""


@dataclass(frozen=True)
class InsightStats:
    inserted: int
    updated: int
    unchanged: int
    deleted: int
    project_count: int
    metadata_updated: bool


class ProjectInsightsStore:
    """High-level API for persisting project insights in SQLite."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        encryption_key: Optional[bytes] = None,
    ) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        _ensure_parent(self.db_path)
        self.serializer = SecureSerializer(encryption_key)
        self._lock = threading.RLock()
        self._apply_migrations()

 
    # DB bootstrap & migrations
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _apply_migrations(self) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL
                    );
                    """
                )
                row = conn.execute(
                    "SELECT MAX(version) FROM schema_migrations;"
                ).fetchone()
                current_version = row[0] or 0
                if current_version < 1:
                    self._apply_initial_schema(conn)
                    conn.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?);",
                        (1, _utcnow()),
                    )
                    current_version = 1
                if current_version < 2:
                    self._apply_audit_schema(conn)
                    conn.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?);",
                        (2, _utcnow()),
                    )
                conn.commit()

    def _apply_initial_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {ZIP_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zip_hash TEXT UNIQUE NOT NULL,
                zip_path TEXT NOT NULL,
                metadata_hash TEXT NOT NULL,
                metadata_encrypted BLOB NOT NULL,
                total_projects INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_pipeline_version TEXT,
                backup_marker TEXT
            );
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {PROJECT_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zip_id INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                slug TEXT NOT NULL,
                project_path TEXT,
                is_git_repo INTEGER NOT NULL DEFAULT 0,
                insight_hash TEXT NOT NULL,
                insights_encrypted BLOB NOT NULL,
                code_files INTEGER NOT NULL DEFAULT 0,
                doc_files INTEGER NOT NULL DEFAULT 0,
                image_files INTEGER NOT NULL DEFAULT 0,
                video_files INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(zip_id) REFERENCES {ZIP_TABLE}(id) ON DELETE CASCADE,
                UNIQUE(zip_id, project_name)
            );
            """
        )
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{PROJECT_TABLE}_zip ON {PROJECT_TABLE}(zip_id);"
        )

    def _apply_audit_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deletion_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                scope TEXT NOT NULL,
                details TEXT,
                deleted_projects INTEGER NOT NULL DEFAULT 0,
                deleted_zips INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """
        )


    # Public API
    def record_pipeline_run(
        self,
        zip_path: str,
        pipeline_result: Dict[str, Any],
        pipeline_version: str = "1.0",
    ) -> InsightStats:
        payload = self._validate_pipeline_result(pipeline_result)
        metadata = payload["zip_metadata"]
        projects = payload["projects"]

        zip_hash = self._derive_zip_hash(zip_path, metadata)
        now = _utcnow()

        with self._lock:
            with self._connect() as conn:
                conn.isolation_level = None  # manual transaction
                try:
                    conn.execute("BEGIN IMMEDIATE;")
                    zip_id, metadata_updated = self._upsert_zip_record(
                        conn,
                        zip_hash,
                        zip_path,
                        metadata,
                        pipeline_version,
                        now,
                    )
                    stats = self._sync_projects(conn, zip_id, projects, now)
                    conn.execute(
                        f"UPDATE {ZIP_TABLE} SET total_projects = ?, updated_at = ? WHERE id = ?;",
                        (stats["project_count"], now, zip_id),
                    )
                    conn.execute("COMMIT;")
                except Exception:
                    conn.execute("ROLLBACK;")
                    raise

        return InsightStats(
            inserted=stats["inserted"],
            updated=stats["updated"],
            unchanged=stats["unchanged"],
            deleted=stats["deleted"],
            project_count=stats["project_count"],
            metadata_updated=metadata_updated,
        )

    def load_project_insight(self, zip_hash: str, project_name: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                f"""
                SELECT p.insights_encrypted
                FROM {PROJECT_TABLE} p
                JOIN {ZIP_TABLE} z ON p.zip_id = z.id
                WHERE z.zip_hash = ? AND p.project_name = ?;
                """,
                (zip_hash, project_name),
            ).fetchone()
            if not row:
                return None
            return self.serializer.decrypt(row[0])

    def load_project_insight_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Load project insight payload by project ID (primary key).
        
        Args:
            project_id: The project.id primary key from the database.
            
        Returns:
            Decrypted project payload dict, or None if project_id not found.
        """
        with self._connect() as conn:
            row = conn.execute(
                f"""
                SELECT insights_encrypted
                FROM {PROJECT_TABLE}
                WHERE id = ?;
                """,
                (project_id,),
            ).fetchone()
            if not row:
                return None
            return self.serializer.decrypt(row[0])

    def list_recent_zipfiles(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT zip_hash, zip_path, total_projects, created_at, updated_at, last_pipeline_version
                FROM {ZIP_TABLE}
                ORDER BY datetime(updated_at) DESC
                LIMIT ?;
                """,
                (limit,),
            ).fetchall()
        results = []
        for row in rows:
            results.append(
                {
                    "zip_hash": row[0],
                    "zip_path": row[1],
                    "total_projects": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "pipeline_version": row[5],
                }
            )
        return results

    def get_zip_metadata(self, zip_hash: str) -> Optional[Dict[str, Any]]:
        """Return decrypted metadata for a stored zip hash."""
        with self._connect() as conn:
            row = conn.execute(
                f"""
                SELECT metadata_encrypted
                FROM {ZIP_TABLE}
                WHERE zip_hash = ?;
                """,
                (zip_hash,),
            ).fetchone()
            if not row:
                return None
            return self.serializer.decrypt(row[0])

    def list_projects_for_zip(self, zip_hash: str) -> List[str]:
        """Return sorted project names associated with the provided zip hash."""
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT p.project_name
                FROM {PROJECT_TABLE} p
                JOIN {ZIP_TABLE} z ON p.zip_id = z.id
                WHERE z.zip_hash = ?
                ORDER BY p.project_name ASC;
                """,
                (zip_hash,),
            ).fetchall()
        return [row[0] for row in rows]

   
    # Deletion API
    def _audit(self, conn: sqlite3.Connection, action: str, scope: str, details: Optional[Dict[str, Any]], deleted_projects: int, deleted_zips: int) -> None:
        conn.execute(
            """
            INSERT INTO deletion_audit (action, scope, details, deleted_projects, deleted_zips, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (action, scope, json.dumps(details or {}), deleted_projects, deleted_zips, _utcnow()),
        )

    def delete_all(self) -> Dict[str, int]:
        """Hard-delete all insights (irreversible). Returns counts."""
        with self._lock:
            with self._connect() as conn:
                conn.isolation_level = None
                conn.execute("BEGIN IMMEDIATE;")
                try:
                    # Count before deletion
                    zcount = conn.execute(f"SELECT COUNT(*) FROM {ZIP_TABLE};").fetchone()[0]
                    pcount = conn.execute(f"SELECT COUNT(*) FROM {PROJECT_TABLE};").fetchone()[0]
                    conn.execute(f"DELETE FROM {ZIP_TABLE};")  # cascades projects
                    self._audit(conn, action="delete_all", scope="all", details=None, deleted_projects=pcount, deleted_zips=zcount)
                    conn.execute("COMMIT;")
                    return {"deleted_projects": pcount, "deleted_zips": zcount}
                except Exception:
                    conn.execute("ROLLBACK;")
                    raise

    def delete_zip(self, zip_hash: str) -> Dict[str, int]:
        """Hard-delete a specific stored run by zip_hash. Preserves other runs."""
        with self._lock:
            with self._connect() as conn:
                conn.isolation_level = None
                conn.execute("BEGIN IMMEDIATE;")
                try:
                    row = conn.execute(f"SELECT id FROM {ZIP_TABLE} WHERE zip_hash = ?;", (zip_hash,)).fetchone()
                    if not row:
                        conn.execute("ROLLBACK;")
                        return {"deleted_projects": 0, "deleted_zips": 0}
                    zip_id = row[0]
                    pcount = conn.execute(f"SELECT COUNT(*) FROM {PROJECT_TABLE} WHERE zip_id = ?;", (zip_id,)).fetchone()[0]
                    conn.execute(f"DELETE FROM {ZIP_TABLE} WHERE id = ?;", (zip_id,))
                    self._audit(conn, action="delete_zip", scope=zip_hash, details={"zip_id": zip_id}, deleted_projects=pcount, deleted_zips=1)
                    conn.execute("COMMIT;")
                    return {"deleted_projects": pcount, "deleted_zips": 1}
                except Exception:
                    conn.execute("ROLLBACK;")
                    raise

    def delete_project(self, zip_hash: str, project_name: str) -> Dict[str, int]:
        """Hard-delete a single project under a given zip. Cleans up zip if empty."""
        with self._lock:
            with self._connect() as conn:
                conn.isolation_level = None
                conn.execute("BEGIN IMMEDIATE;")
                try:
                    row = conn.execute(f"SELECT id FROM {ZIP_TABLE} WHERE zip_hash = ?;", (zip_hash,)).fetchone()
                    if not row:
                        conn.execute("ROLLBACK;")
                        return {"deleted_projects": 0, "deleted_zips": 0}
                    zip_id = row[0]
                    prow = conn.execute(
                        f"SELECT id FROM {PROJECT_TABLE} WHERE zip_id = ? AND project_name = ?;",
                        (zip_id, project_name),
                    ).fetchone()
                    if not prow:
                        conn.execute("ROLLBACK;")
                        return {"deleted_projects": 0, "deleted_zips": 0}
                    conn.execute(f"DELETE FROM {PROJECT_TABLE} WHERE id = ?;", (prow[0],))
                    # If no projects remain, delete the zip row too
                    remaining = conn.execute(f"SELECT COUNT(*) FROM {PROJECT_TABLE} WHERE zip_id = ?;", (zip_id,)).fetchone()[0]
                    zdel = 0
                    if remaining == 0:
                        conn.execute(f"DELETE FROM {ZIP_TABLE} WHERE id = ?;", (zip_id,))
                        zdel = 1
                    self._audit(conn, action="delete_project", scope=f"{zip_hash}:{project_name}", details={"zip_id": zip_id}, deleted_projects=1, deleted_zips=zdel)
                    conn.execute("COMMIT;")
                    return {"deleted_projects": 1, "deleted_zips": zdel}
                except Exception:
                    conn.execute("ROLLBACK;")
                    raise

    def backup(self, backup_path: str) -> str:
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database does not exist at {self.db_path}")
        target = Path(backup_path)
        if target.is_dir():
            target = target / f"insights_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        _ensure_parent(str(target))
        shutil.copy2(self.db_path, target)
        self._mark_backup()
        return str(target)

    def restore(self, backup_path: str) -> None:
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        _ensure_parent(self.db_path)
        temp_target = f"{self.db_path}.restoring"
        shutil.copy2(backup_path, temp_target)
        shutil.move(temp_target, self.db_path)
        self._apply_migrations()

    def purge_expired_records(self, retention_days: int, keep_recent: int = 5) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    f"""
                    SELECT id, updated_at
                    FROM {ZIP_TABLE}
                    ORDER BY datetime(updated_at) DESC;
                    """
                ).fetchall()
                keep_ids = {row[0] for row in rows[:keep_recent]}
                purge_ids: List[int] = []
                for row in rows:
                    if row[0] in keep_ids:
                        continue
                    updated_at = _iso_to_datetime(row[1])
                    if updated_at < cutoff:
                        purge_ids.append(row[0])
                if not purge_ids:
                    return 0
                placeholders = ",".join("?" for _ in purge_ids)
                conn.execute(
                    f"DELETE FROM {ZIP_TABLE} WHERE id IN ({placeholders});",
                    purge_ids,
                )
                conn.commit()
        return len(purge_ids)

    # Internal helpers
    def _validate_pipeline_result(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise PayloadValidationError("Pipeline output must be a dict.")
        metadata = payload.get("zip_metadata")
        if not isinstance(metadata, dict):
            raise PayloadValidationError("zip_metadata is required.")
        expected_meta = {"root_name", "file_count", "total_uncompressed_bytes", "total_compressed_bytes"}
        missing = [field for field in expected_meta if field not in metadata]
        if missing:
            raise PayloadValidationError(f"Missing metadata fields: {', '.join(missing)}")
        projects = payload.get("projects")
        if not isinstance(projects, dict) or not projects:
            raise PayloadValidationError("projects payload must be a non-empty mapping.")
        cleaned: Dict[str, Dict[str, Any]] = {}
        for name, data in projects.items():
            if not isinstance(data, dict):
                continue
            cleaned[name] = data
        if not cleaned:
            raise PayloadValidationError("No valid project payloads found.")
        return {"zip_metadata": metadata, "projects": cleaned}

    def _derive_zip_hash(self, zip_path: str, metadata: Dict[str, Any]) -> str:
        hasher = hashlib.sha256()
        hasher.update(Path(zip_path).name.encode("utf-8"))
        hasher.update(str(metadata.get("file_count", 0)).encode("utf-8"))
        hasher.update(str(metadata.get("total_uncompressed_bytes", 0)).encode("utf-8"))
        hasher.update(str(metadata.get("total_compressed_bytes", 0)).encode("utf-8"))
        return hasher.hexdigest()

    def _hash_dict(self, payload: Dict[str, Any]) -> str:
        normalized = _canonical_dumps(payload)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _slugify(self, name: str) -> str:
        safe = "".join(ch if ch.isalnum() else "-" for ch in name.lower())
        return "-".join(filter(None, safe.split("-")))[:128] or "project"

    def _upsert_zip_record(
        self,
        conn: sqlite3.Connection,
        zip_hash: str,
        zip_path: str,
        metadata: Dict[str, Any],
        pipeline_version: str,
        timestamp: str,
    ) -> Tuple[int, bool]:
        metadata_hash = self._hash_dict(metadata)
        encrypted = self.serializer.encrypt(metadata)
        row = conn.execute(
            f"SELECT id, metadata_hash FROM {ZIP_TABLE} WHERE zip_hash = ?;",
            (zip_hash,),
        ).fetchone()
        if row:
            zip_id, existing_hash = row
            if existing_hash != metadata_hash:
                conn.execute(
                    f"""
                    UPDATE {ZIP_TABLE}
                    SET metadata_encrypted = ?, metadata_hash = ?, updated_at = ?, zip_path = ?, last_pipeline_version = ?
                    WHERE id = ?;
                    """,
                    (encrypted, metadata_hash, timestamp, zip_path, pipeline_version, zip_id),
                )
                metadata_updated = True
            else:
                conn.execute(
                    f"UPDATE {ZIP_TABLE} SET updated_at = ?, zip_path = ?, last_pipeline_version = ? WHERE id = ?;",
                    (timestamp, zip_path, pipeline_version, zip_id),
                )
                metadata_updated = False
            return zip_id, metadata_updated

        conn.execute(
            f"""
            INSERT INTO {ZIP_TABLE} (
                zip_hash, zip_path, metadata_hash, metadata_encrypted, total_projects,
                created_at, updated_at, last_pipeline_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (zip_hash, zip_path, metadata_hash, encrypted, 0, timestamp, timestamp, pipeline_version),
        )
        zip_id = conn.execute("SELECT last_insert_rowid();").fetchone()[0]
        return zip_id, True

    def _summarize_counts(self, project_payload: Dict[str, Any]) -> Tuple[int, int, int, int]:
        categorized = project_payload.get("categorized_contents") or {}
        code_files = len(categorized.get("code", []))
        doc_files = len(categorized.get("documentation", []))
        image_files = len(categorized.get("images", []))
        other = categorized.get("other", [])
        video_files = len([p for p in other if Path(p).suffix.lower() in ArtifactVideoHint.EXTENSIONS])
        return code_files, doc_files, image_files, video_files

    def _sync_projects(
        self,
        conn: sqlite3.Connection,
        zip_id: int,
        projects: Dict[str, Dict[str, Any]],
        timestamp: str,
    ) -> Dict[str, int]:
        stats = {"inserted": 0, "updated": 0, "unchanged": 0, "deleted": 0}
        existing_rows = conn.execute(
            f"""
            SELECT project_name, id, insight_hash
            FROM {PROJECT_TABLE}
            WHERE zip_id = ?;
            """,
            (zip_id,),
        ).fetchall()
        existing_map = {row[0]: (row[1], row[2]) for row in existing_rows}
        active_names = set()

        for project_name, payload in projects.items():
            slug = self._slugify(project_name)
            payload_copy = dict(payload)
            payload_copy["project_name"] = project_name
            payload_copy["zip_id"] = zip_id
            insight_hash = self._hash_dict(payload_copy)
            encrypted = self.serializer.encrypt(payload_copy)
            code_files, doc_files, image_files, video_files = self._summarize_counts(payload)
            is_git = 1 if payload.get("is_git_repo") else 0
            project_path = payload.get("project_path")
            active_names.add(project_name)

            if project_name in existing_map:
                project_id, existing_hash = existing_map[project_name]
                if existing_hash == insight_hash:
                    conn.execute(
                        f"UPDATE {PROJECT_TABLE} SET updated_at = ? WHERE id = ?;",
                        (timestamp, project_id),
                    )
                    stats["unchanged"] += 1
                else:
                    conn.execute(
                        f"""
                        UPDATE {PROJECT_TABLE}
                        SET slug = ?, project_path = ?, is_git_repo = ?, insight_hash = ?,
                            insights_encrypted = ?, code_files = ?, doc_files = ?, image_files = ?, video_files = ?, updated_at = ?
                        WHERE id = ?;
                        """,
                        (
                            slug,
                            project_path,
                            is_git,
                            insight_hash,
                            encrypted,
                            code_files,
                            doc_files,
                            image_files,
                            video_files,
                            timestamp,
                            project_id,
                        ),
                    )
                    stats["updated"] += 1
            else:
                conn.execute(
                    f"""
                    INSERT INTO {PROJECT_TABLE} (
                        zip_id, project_name, slug, project_path, is_git_repo, insight_hash,
                        insights_encrypted, code_files, doc_files, image_files, video_files,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        zip_id,
                        project_name,
                        slug,
                        project_path,
                        is_git,
                        insight_hash,
                        encrypted,
                        code_files,
                        doc_files,
                        image_files,
                        video_files,
                        timestamp,
                        timestamp,
                    ),
                )
                stats["inserted"] += 1

        obsolete_names = set(existing_map.keys()) - active_names
        if obsolete_names:
            obsolete_list = sorted(obsolete_names)
            placeholders = ",".join("?" for _ in obsolete_list)
            conn.execute(
                f"DELETE FROM {PROJECT_TABLE} WHERE zip_id = ? AND project_name IN ({placeholders});",
                (zip_id, *obsolete_list),
            )
            stats["deleted"] += len(obsolete_list)

        stats["project_count"] = len(active_names)
        return stats

    def _mark_backup(self) -> None:  
        try:
            with self._connect() as conn:
                conn.execute(
                    f"UPDATE {ZIP_TABLE} SET backup_marker = ?;",
                    (_utcnow(),),
                )
                conn.commit()
        except Exception:

            pass


class ArtifactVideoHint:
    """Utility container for video extensions used by the orchestrator."""

    EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".wmv"}
