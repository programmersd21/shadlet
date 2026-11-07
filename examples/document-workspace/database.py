"""SQLite persistence for document sections."""

from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path
from typing import TypedDict

try:
    from .models import REVIEWERS, SECTION_NAMES, SECTION_TYPES, STATUSES
except ImportError:
    from models import REVIEWERS, SECTION_NAMES, SECTION_TYPES, STATUSES

DB_PATH = Path(__file__).resolve().parent / "data" / "document_workspace.db"


class SectionValues(TypedDict):
    name: str
    section_type: str
    status: str
    target: int
    limit: int
    reviewer: str


class DatabaseError(RuntimeError):
    """Raised when a database operation cannot be completed."""


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        try:
            with contextlib.closing(self.connect()) as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        section_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        target INTEGER NOT NULL,
                        limit_value INTEGER NOT NULL,
                        reviewer TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sections_status ON sections(status)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sections_type ON sections(section_type)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sections_reviewer ON sections(reviewer)"
                )
                count = connection.execute("SELECT COUNT(*) FROM sections").fetchone()[
                    0
                ]
                if count == 0:
                    self._seed(connection)
        except sqlite3.Error as error:
            raise DatabaseError(f"could not initialize database: {error}") from error

    def _seed(self, connection: sqlite3.Connection) -> None:
        rows = []
        for index in range(68):
            base_name = SECTION_NAMES[index % len(SECTION_NAMES)]
            name = (
                base_name if index < len(SECTION_NAMES) else f"{base_name} {index + 1}"
            )
            rows.append(
                (
                    name,
                    SECTION_TYPES[index % len(SECTION_TYPES)],
                    STATUSES[index % len(STATUSES)],
                    100 + (index * 7) % 900,
                    20 + (index * 13) % 80,
                    REVIEWERS[index % len(REVIEWERS)],
                )
            )
        connection.executemany(
            """
            INSERT INTO sections (name, section_type, status, target, limit_value, reviewer)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    def list_sections(
        self,
        *,
        search: str = "",
        status: str | None = None,
        section_type: str | None = None,
        sort_key: str = "name",
        sort_direction: str = "asc",
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[dict[str, object]], int]:
        allowed_sort = {
            "name",
            "section_type",
            "status",
            "target",
            "limit_value",
            "reviewer",
        }
        if sort_key not in allowed_sort:
            sort_key = "name"
        direction = "DESC" if sort_direction.lower() == "desc" else "ASC"
        where = []
        params: list[object] = []
        if search:
            where.append("(name LIKE ? OR section_type LIKE ? OR reviewer LIKE ?)")
            needle = f"%{search}%"
            params.extend([needle, needle, needle])
        if status:
            where.append("status = ?")
            params.append(status)
        if section_type:
            where.append("section_type = ?")
            params.append(section_type)
        clause = " WHERE " + " AND ".join(where) if where else ""
        try:
            with contextlib.closing(self.connect()) as connection:
                total = connection.execute(
                    f"SELECT COUNT(*) FROM sections{clause}", params
                ).fetchone()[0]
                rows = connection.execute(
                    f"""
                    SELECT id, name, section_type, status, target, limit_value, reviewer
                    FROM sections{clause}
                    ORDER BY {sort_key} {direction}
                    LIMIT ? OFFSET ?
                    """,
                    [*params, limit, offset],
                ).fetchall()
                return [dict(row) for row in rows], int(total)
        except sqlite3.Error as error:
            raise DatabaseError(f"could not list sections: {error}") from error

    def get_section(self, section_id: int) -> dict[str, object] | None:
        try:
            with contextlib.closing(self.connect()) as connection:
                row = connection.execute(
                    """
                    SELECT id, name, section_type, status, target, limit_value, reviewer
                    FROM sections WHERE id = ?
                    """,
                    (section_id,),
                ).fetchone()
                return dict(row) if row is not None else None
        except sqlite3.Error as error:
            raise DatabaseError(f"could not read section: {error}") from error

    def create_section(self, values: SectionValues) -> int:
        try:
            with contextlib.closing(self.connect()) as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO sections (name, section_type, status, target, limit_value, reviewer)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(values["name"]),
                        str(values["section_type"]),
                        str(values["status"]),
                        int(values["target"]),
                        int(values["limit"]),
                        str(values["reviewer"]),
                    ),
                )
                if cursor.lastrowid is None:
                    raise DatabaseError(
                        "could not create section: SQLite did not return an inserted row ID"
                    )
                return cursor.lastrowid
        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            raise DatabaseError(f"could not create section: {error}") from error

    def update_section(self, section_id: int, values: SectionValues) -> None:
        try:
            with contextlib.closing(self.connect()) as connection:
                connection.execute(
                    """
                    UPDATE sections
                    SET name = ?, section_type = ?, status = ?, target = ?,
                        limit_value = ?, reviewer = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        str(values["name"]),
                        str(values["section_type"]),
                        str(values["status"]),
                        int(values["target"]),
                        int(values["limit"]),
                        str(values["reviewer"]),
                        section_id,
                    ),
                )
        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            raise DatabaseError(f"could not update section: {error}") from error

    def delete_section(self, section_id: int) -> None:
        try:
            with contextlib.closing(self.connect()) as connection:
                connection.execute("DELETE FROM sections WHERE id = ?", (section_id,))
        except sqlite3.Error as error:
            raise DatabaseError(f"could not delete section: {error}") from error

    def delete_sections(self, section_ids: list[int]) -> None:
        if not section_ids:
            return
        placeholders = ",".join("?" for _ in section_ids)
        try:
            with contextlib.closing(self.connect()) as connection:
                connection.execute(
                    f"DELETE FROM sections WHERE id IN ({placeholders})", section_ids
                )
        except sqlite3.Error as error:
            raise DatabaseError(f"could not delete sections: {error}") from error

    def summary_by_type(self) -> list[dict[str, object]]:
        try:
            with contextlib.closing(self.connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT section_type,
                           COUNT(*) AS total,
                           SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) AS done
                    FROM sections
                    GROUP BY section_type
                    ORDER BY section_type
                    """
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as error:
            raise DatabaseError(f"could not summarize sections: {error}") from error

    def summary_by_reviewer(self) -> list[dict[str, object]]:
        try:
            with contextlib.closing(self.connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT reviewer,
                           COUNT(*) AS assigned,
                           SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) AS done,
                           SUM(CASE WHEN status <> 'Done' THEN 1 ELSE 0 END) AS open
                    FROM sections
                    GROUP BY reviewer
                    ORDER BY reviewer
                    """
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as error:
            raise DatabaseError(f"could not summarize reviewers: {error}") from error

    def kpis(self) -> dict[str, int]:
        try:
            with contextlib.closing(self.connect()) as connection:
                total = connection.execute("SELECT COUNT(*) FROM sections").fetchone()[
                    0
                ]
                done = connection.execute(
                    "SELECT COUNT(*) FROM sections WHERE status = 'Done'"
                ).fetchone()[0]
                in_progress = total - done
                return {
                    "total": int(total),
                    "done": int(done),
                    "in_progress": int(in_progress),
                }
        except sqlite3.Error as error:
            raise DatabaseError(f"could not read summary: {error}") from error


__all__ = ["DB_PATH", "Database", "DatabaseError"]
