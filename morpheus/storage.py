"""
morpheus/storage.py — SQLite database run history storage for Morpheus.

Saves, retrieves, lists, and deletes execution run records.
Database path is determined by MORPHEUS_DB_PATH environment variable,
defaulting to ~/.morpheus/history.db.

Dependency rules: This module imports nothing from inside morpheus.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunRecord:
    """A complete record of one Morpheus run, stored in SQLite."""

    run_id: str  # UUID4 string — generated at save time
    filepath: str  # Absolute path of the traced file
    timestamp: float  # Unix timestamp when the run was saved
    mode: str  # "narrator", "prophecy", "spy", "teach", "oracle"
    chapters: str  # JSON-serialized list of chapter titles and event counts
    narrations: str  # JSON-serialized list of narration strings per chapter
    duration_ms: float  # Total run duration in milliseconds
    event_count: int  # Total number of TraceEvents captured
    error: str = ""  # Error message if the traced script crashed, else empty string


class MorpheusStorage:
    """
    Manages the SQLite database for Morpheus run history.
    Database is created automatically if it does not exist.
    Default location: ~/.morpheus/history.db
    """

    def __init__(self, db_path: str = "~/.morpheus/history.db") -> None:
        """
        Initialize storage and create the database + table if they don't exist.

        Args:
            db_path: Path to the SQLite database file.
                     Can be overridden via MORPHEUS_DB_PATH env var.
                     Parent directories are created automatically.
        """
        # Override with environment variable if present
        env_path = os.getenv("MORPHEUS_DB_PATH")
        actual_path = env_path if env_path is not None else db_path

        # Handle in-memory database as a special case
        if actual_path == ":memory:":
            self.db_path = ":memory:"
            self._conn = sqlite3.connect(":memory:", uri=True)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    filepath TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    mode TEXT NOT NULL,
                    chapters TEXT NOT NULL,
                    narrations TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    event_count INTEGER NOT NULL,
                    error TEXT DEFAULT ''
                )
            """)
            return

        # Resolve path, handling ~ for home directory
        resolved_path = Path(actual_path).expanduser().resolve()
        self.db_path: str = str(resolved_path)

        # Ensure parent directories exist
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                filepath TEXT NOT NULL,
                timestamp REAL NOT NULL,
                mode TEXT NOT NULL,
                chapters TEXT NOT NULL,
                narrations TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                event_count INTEGER NOT NULL,
                error TEXT DEFAULT ''
            )
        """)

    def _cursor(self) -> sqlite3.Cursor:
        return self._conn.cursor()

    def save_run(self, record: RunRecord) -> str:
        """
        Save a completed run record to the database.
        Generates a new UUID for run_id if record.run_id is empty.

        Args:
            record: Populated RunRecord dataclass.

        Returns:
            The run_id string of the saved record.

        Raises:
            sqlite3.Error: If the database write fails.
        """
        if not record.run_id:
            record.run_id = str(uuid.uuid4())

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO runs (
                    run_id, filepath, timestamp, mode, chapters,
                    narrations, duration_ms, event_count, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    record.filepath,
                    record.timestamp,
                    record.mode,
                    record.chapters,
                    record.narrations,
                    record.duration_ms,
                    record.event_count,
                    record.error,
                ),
            )

        return record.run_id

    def get_run(self, run_id: str) -> RunRecord:
        """
        Retrieve a single run by its ID.

        Args:
            run_id: UUID string returned by save_run().

        Returns:
            RunRecord dataclass populated from the database row.

        Raises:
            KeyError: If no run with this ID exists.
            sqlite3.Error: If the database read fails.
        """
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT run_id, filepath, timestamp, mode, chapters,
                   narrations, duration_ms, event_count, error
            FROM runs
            WHERE run_id = ?
            """,
            (run_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"No run found with ID: {run_id}")

        return RunRecord(
            run_id=row[0],
            filepath=row[1],
            timestamp=row[2],
            mode=row[3],
            chapters=row[4],
            narrations=row[5],
            duration_ms=row[6],
            event_count=row[7],
            error=row[8],
        )

    def list_runs(self, limit: int = 20) -> list[RunRecord]:
        """
        Return the most recent runs, newest first.

        Args:
            limit: Maximum number of runs to return. Default 20.

        Returns:
            List of RunRecord objects ordered by timestamp descending.
            Returns empty list if no runs exist.
        """
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT run_id, filepath, timestamp, mode, chapters,
                   narrations, duration_ms, event_count, error
            FROM runs
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        results: list[RunRecord] = []
        for row in rows:
            results.append(
                RunRecord(
                    run_id=row[0],
                    filepath=row[1],
                    timestamp=row[2],
                    mode=row[3],
                    chapters=row[4],
                    narrations=row[5],
                    duration_ms=row[6],
                    event_count=row[7],
                    error=row[8],
                )
            )
        return results

    def delete_run(self, run_id: str) -> bool:
        """
        Delete a run record by ID.

        Args:
            run_id: UUID string of the run to delete.

        Returns:
            True if a record was deleted. False if no record with that ID exists.
        """
        with self._conn:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
            return cursor.rowcount > 0
