"""
project_filter.py
-----------------
Advanced project filtering and search capabilities for insights.
Supports filtering by dates, languages, skills, project types, success metrics,
and custom sorting with saved filter presets.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


class SortBy(str, Enum):
    """Sorting options for filtered projects."""
    IMPORTANCE = "importance"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    LOC_DESC = "loc_desc"
    LOC_ASC = "loc_asc"
    COMMITS_DESC = "commits_desc"
    COMMITS_ASC = "commits_asc"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    CONTRIBUTORS_DESC = "contributors_desc"
    CONTRIBUTORS_ASC = "contributors_asc"


class ProjectType(str, Enum):
    """Project type classifications."""
    INDIVIDUAL = "individual"
    COLLABORATIVE = "collaborative"
    ALL = "all"


@dataclass
class DateRange:
    """Date range for filtering projects."""
    start: Optional[str] = None  # ISO format date
    end: Optional[str] = None    # ISO format date

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {"start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DateRange:
        return cls(start=data.get("start"), end=data.get("end"))


@dataclass
class SuccessMetrics:
    """Success metric thresholds for filtering."""
    min_lines: Optional[int] = None
    max_lines: Optional[int] = None
    min_commits: Optional[int] = None
    max_commits: Optional[int] = None
    min_contributors: Optional[int] = None
    max_contributors: Optional[int] = None
    min_files: Optional[int] = None
    max_files: Optional[int] = None

    def to_dict(self) -> Dict[str, Optional[int]]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SuccessMetrics:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ProjectFilter:
    """
    Comprehensive project filter configuration.
    
    All filter criteria are optional and combined with AND logic.
    """
    # Date filtering
    date_range: Optional[DateRange] = None
    
    # Technology filtering
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    
    # Project characteristics
    project_type: ProjectType = ProjectType.ALL
    complexity: Optional[str] = None  # e.g., "simple", "moderate", "complex"
    
    # Success metrics
    metrics: Optional[SuccessMetrics] = None
    
    # Text search
    search_text: Optional[str] = None  # Searches name, description, tagline
    
    # Sorting
    sort_by: SortBy = SortBy.DATE_DESC
    limit: Optional[int] = None
    offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary for JSON serialization."""
        return {
            "date_range": self.date_range.to_dict() if self.date_range else None,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "skills": self.skills,
            "project_type": self.project_type.value,
            "complexity": self.complexity,
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "search_text": self.search_text,
            "sort_by": self.sort_by.value,
            "limit": self.limit,
            "offset": self.offset,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectFilter:
        """Create filter from dictionary."""
        return cls(
            date_range=DateRange.from_dict(data["date_range"]) if data.get("date_range") else None,
            languages=data.get("languages", []),
            frameworks=data.get("frameworks", []),
            skills=data.get("skills", []),
            project_type=ProjectType(data.get("project_type", "all")),
            complexity=data.get("complexity"),
            metrics=SuccessMetrics.from_dict(data["metrics"]) if data.get("metrics") else None,
            search_text=data.get("search_text"),
            sort_by=SortBy(data.get("sort_by", "date_desc")),
            limit=data.get("limit"),
            offset=data.get("offset", 0),
        )


@dataclass
class FilterPreset:
    """Saved filter configuration with metadata."""
    name: str
    description: Optional[str]
    filter_config: ProjectFilter
    created_at: str
    updated_at: str
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "filter_config": self.filter_config.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FilterPreset:
        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description"),
            filter_config=ProjectFilter.from_dict(data["filter_config"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


class ProjectFilterEngine:
    """
    Engine for filtering and searching projects based on various criteria.
    Integrates with the existing ProjectInsightsStore database schema.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_presets_table()

    def _ensure_presets_table(self) -> None:
        """Create filter presets table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS filter_presets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    filter_config TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            conn.commit()

    def apply_filter(self, filter_config: ProjectFilter) -> List[Dict[str, Any]]:
        """
        Apply filter configuration and return matching projects.
        
        Returns list of project dictionaries with all available fields.
        """
        query, params = self._build_query(filter_config)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
        
        return results

    def _build_query(self, filter_config: ProjectFilter) -> Tuple[str, List[Any]]:
        """Build SQL query from filter configuration."""
        params: List[Any] = []
        
        # Base query joins all relevant tables
        query = """
            SELECT DISTINCT
                pi.id as project_info_id,
                COALESCE(pi.project_name, p.project_name) as project_name,
                p.slug,
                p.root_path,
                pi.created_at as project_created_at,
                pi.updated_at as project_updated_at,
                pi.total_files,
                pi.total_lines,
                pi.total_commits,
                pi.total_contributors,
                pi.is_git_repo,
                port.tagline,
                port.description,
                port.project_type,
                port.complexity,
                port.is_collaborative,
                port.summary
            FROM project_info pi
            JOIN projects p ON pi.project_id = p.id
            JOIN ingest i ON i.id = pi.ingest_id
            LEFT JOIN portfolio_insights port ON port.project_info_id = pi.id
            WHERE 1=1
              AND pi.is_deleted = 0
              AND i.id = (
                SELECT id FROM ingest i2
                WHERE i2.source_hash = i.source_hash
                ORDER BY i2.id DESC
                LIMIT 1
            )
        """
        
        # Date range filtering
        if filter_config.date_range:
            if filter_config.date_range.start:
                query += " AND p.created_at >= ?"
                params.append(filter_config.date_range.start)
            if filter_config.date_range.end:
                query += " AND p.created_at <= ?"
                params.append(filter_config.date_range.end)
        
        # Project type filtering
        if filter_config.project_type != ProjectType.ALL:
            is_collaborative = 1 if filter_config.project_type == ProjectType.COLLABORATIVE else 0
            query += " AND port.is_collaborative = ?"
            params.append(is_collaborative)
        
        # Complexity filtering
        if filter_config.complexity:
            query += " AND port.complexity = ?"
            params.append(filter_config.complexity)
        
        # Success metrics filtering
        if filter_config.metrics:
            m = filter_config.metrics
            if m.min_lines is not None:
                query += " AND pi.total_lines >= ?"
                params.append(m.min_lines)
            if m.max_lines is not None:
                query += " AND pi.total_lines <= ?"
                params.append(m.max_lines)
            if m.min_commits is not None:
                query += " AND pi.total_commits >= ?"
                params.append(m.min_commits)
            if m.max_commits is not None:
                query += " AND pi.total_commits <= ?"
                params.append(m.max_commits)
            if m.min_contributors is not None:
                query += " AND pi.total_contributors >= ?"
                params.append(m.min_contributors)
            if m.max_contributors is not None:
                query += " AND pi.total_contributors <= ?"
                params.append(m.max_contributors)
            if m.min_files is not None:
                query += " AND pi.total_files >= ?"
                params.append(m.min_files)
            if m.max_files is not None:
                query += " AND pi.total_files <= ?"
                params.append(m.max_files)
        
        # Text search across name, description, tagline
        if filter_config.search_text:
            search_pattern = f"%{filter_config.search_text}%"
            query += """ AND (
                COALESCE(pi.project_name, p.project_name) LIKE ? OR
                port.description LIKE ? OR
                port.tagline LIKE ? OR
                port.summary LIKE ?
            )"""
            params.extend([search_pattern] * 4)
        
        # Technology filtering (languages, frameworks, skills)
        if filter_config.languages or filter_config.frameworks or filter_config.skills:
            query = self._add_tag_filters(query, filter_config, params)
        
        # Apply sorting
        query += self._build_sort_clause(filter_config.sort_by)
        
        # Apply pagination (OFFSET requires LIMIT in SQLite)
        if filter_config.limit:
            query += " LIMIT ?"
            params.append(filter_config.limit)
            if filter_config.offset:
                query += " OFFSET ?"
                params.append(filter_config.offset)
        elif filter_config.offset:
            query += " LIMIT -1 OFFSET ?"
            params.append(filter_config.offset)
        
        return query, params

    def _add_tag_filters(self, query: str, filter_config: ProjectFilter, params: List[Any]) -> str:
        """Add filtering for tags (languages, frameworks, skills) using tags_json on project_info."""
        tag_conditions = []

        if filter_config.languages:
            tag_conditions.append(("language", filter_config.languages))
        if filter_config.frameworks:
            tag_conditions.append(("framework", filter_config.frameworks))
        if filter_config.skills:
            tag_conditions.append(("skill", filter_config.skills))

        if tag_conditions:
            query += """ AND pi.id IN (
                SELECT pi2.id
                FROM project_info pi2, json_each(pi2.tags_json) je
                WHERE pi2.tags_json IS NOT NULL AND (
            """

            or_clauses = []
            for tag_type, tag_names in tag_conditions:
                placeholders = ",".join("?" * len(tag_names))
                or_clauses.append(
                    f"(json_extract(je.value, '$.tag_type') = ? "
                    f"AND LOWER(json_extract(je.value, '$.name')) IN ({placeholders}))"
                )
                params.append(tag_type)
                params.extend([name.lower() for name in tag_names])

            query += " OR ".join(or_clauses)
            query += "))"

        return query

    def _build_sort_clause(self, sort_by: SortBy) -> str:
        """Build ORDER BY clause based on sort configuration."""
        sort_map = {
            SortBy.DATE_DESC: "p.created_at DESC",
            SortBy.DATE_ASC: "p.created_at ASC",
            SortBy.LOC_DESC: "pi.total_lines DESC",
            SortBy.LOC_ASC: "pi.total_lines ASC",
            SortBy.COMMITS_DESC: "pi.total_commits DESC",
            SortBy.COMMITS_ASC: "pi.total_commits ASC",
            SortBy.NAME_ASC: "p.project_name ASC",
            SortBy.NAME_DESC: "p.project_name DESC",
            SortBy.CONTRIBUTORS_DESC: "pi.total_contributors DESC",
            SortBy.CONTRIBUTORS_ASC: "pi.total_contributors ASC",
            SortBy.IMPORTANCE: "pi.total_commits DESC, pi.total_lines DESC",
        }
        return f" ORDER BY {sort_map.get(sort_by, 'p.created_at DESC')}"

    # Preset management methods
    def save_preset(self, name: str, filter_config: ProjectFilter, description: Optional[str] = None) -> int:
        """Save a filter preset. Returns the preset ID."""
        now = datetime.utcnow().isoformat()
        config_json = json.dumps(filter_config.to_dict())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO filter_presets (name, description, filter_config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    description = excluded.description,
                    filter_config = excluded.filter_config,
                    updated_at = excluded.updated_at
                RETURNING id
            """, (name, description, config_json, now, now))
            preset_id = cursor.fetchone()[0]
            conn.commit()
        
        return preset_id

    def get_preset(self, preset_id: int) -> Optional[FilterPreset]:
        """Get a specific filter preset by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM filter_presets WHERE id = ?",
                (preset_id,)
            )
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_preset(dict(row))

    def get_preset_by_name(self, name: str) -> Optional[FilterPreset]:
        """Get a specific filter preset by name."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM filter_presets WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_preset(dict(row))

    def list_presets(self) -> List[FilterPreset]:
        """List all saved filter presets."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM filter_presets ORDER BY updated_at DESC"
            )
            rows = [dict(row) for row in cursor.fetchall()]
        
        return [self._row_to_preset(row) for row in rows]

    def delete_preset(self, preset_id: int) -> bool:
        """Delete a filter preset. Returns True if deleted, False if not found."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM filter_presets WHERE id = ?",
                (preset_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_preset(self, row: Dict[str, Any]) -> FilterPreset:
        """Convert database row to FilterPreset object."""
        filter_config = ProjectFilter.from_dict(json.loads(row["filter_config"]))
        return FilterPreset(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            filter_config=filter_config,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def search_projects(self, search_text: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Simple full-text search across project names, descriptions, and skills.
        Returns up to `limit` matching projects.
        """
        filter_config = ProjectFilter(
            search_text=search_text,
            sort_by=SortBy.IMPORTANCE,
            limit=limit
        )
        return self.apply_filter(filter_config)

    def get_skill_trends(self, skill: str) -> List[Dict[str, Any]]:
        """Get skill usage trends over time."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT
                    strftime('%Y-%m', pi.created_at) as month,
                    COUNT(*) as project_count,
                    SUM(pi.total_lines) as total_lines
                FROM project_info pi, json_each(pi.tags_json) je
                WHERE pi.tags_json IS NOT NULL
                  AND LOWER(json_extract(je.value, '$.name')) = LOWER(?)
                GROUP BY month
                ORDER BY month DESC
                LIMIT 24
            """, (skill,))

            return [{"month": row[0], "project_count": row[1], "total_lines": row[2] or 0} for row in cursor.fetchall()]

    def get_skill_progression(self) -> Dict[str, Any]:
        """Get skill progression and usage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT
                    json_extract(je.value, '$.name') as skill,
                    COUNT(DISTINCT pi.id) as projects_count,
                    MIN(strftime('%Y-%m-%d', pi.created_at)) as first_seen,
                    MAX(strftime('%Y-%m-%d', pi.created_at)) as last_seen,
                    SUM(pi.total_lines) as total_lines
                FROM project_info pi, json_each(pi.tags_json) je
                WHERE pi.tags_json IS NOT NULL
                  AND json_extract(je.value, '$.tag_type') = 'skill'
                GROUP BY skill
                ORDER BY projects_count DESC, total_lines DESC
            """)

            return {row[0]: {
                "projects_count": row[1],
                "first_seen": row[2],
                "last_seen": row[3],
                "total_lines": row[4] or 0
            } for row in cursor.fetchall()}
