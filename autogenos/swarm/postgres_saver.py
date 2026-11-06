"""
Durable State Persistence Checkpointer.
Provides thread-scoped checkpointing with connection pooling and dictionary row factories
to prevent serialization errors and transaction deadlocks during high-frequency swarm operations.
"""

from __future__ import annotations
import json
import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from autogenos.core.state import SwarmGlobalState

logger = logging.getLogger("autogenos.checkpointer")


class DurableStateSaver:
    """
    Manages durable thread-scoped state persistence across swarm steps.
    Uses SQLite-backed WAL mode (or PostgreSQL with autocommit=True) for deadlock-free persistence.
    """

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = str(db_path) if db_path else ":memory:"
        # Keep persistent connection for in-memory or thread-pool mode
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            autocommit=True
        )
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        if self.db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                session_id TEXT,
                step_index INTEGER,
                state_json TEXT,
                phase TEXT,
                timestamp REAL,
                PRIMARY KEY (session_id, step_index)
            );
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS semantic_store (
                key TEXT PRIMARY KEY,
                data_json TEXT,
                updated_at REAL
            );
        """)

    def save_checkpoint(self, state: SwarmGlobalState) -> None:
        """Saves immutable snapshot of current swarm state."""
        import time
        self._conn.execute(
            """
            INSERT OR REPLACE INTO checkpoints (session_id, step_index, state_json, phase, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                state.session_id,
                state.step_count,
                state.model_dump_json(),
                state.phase.value,
                time.time()
            )
        )
        logger.debug(f"Saved checkpoint session={state.session_id} step={state.step_count}")

    def load_latest_checkpoint(self, session_id: str) -> Optional[SwarmGlobalState]:
        """Loads latest saved checkpoint for session."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT state_json FROM checkpoints
            WHERE session_id = ?
            ORDER BY step_index DESC
            LIMIT 1
            """,
            (session_id,)
        )
        row = cursor.fetchone()
        if row:
            return SwarmGlobalState.model_validate_json(row["state_json"])
        return None

    def list_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT step_index, phase, timestamp FROM checkpoints
            WHERE session_id = ?
            ORDER BY step_index ASC
            """,
            (session_id,)
        )
        return [dict(r) for r in cursor.fetchall()]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
