"""SQLite persistence for CareerPilot sessions."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    def __init__(self, db_url: str | None = None) -> None:
        settings = get_settings()
        url = db_url or settings.database_url
        # sqlite:///./data/careerpilot.db
        path = url.replace("sqlite:///", "")
        self.db_path = Path(path)
        if not self.db_path.is_absolute():
            # Resolve relative to backend working directory
            self.db_path = Path.cwd() / self.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    user_goal TEXT,
                    target_role TEXT,
                    experience_level TEXT,
                    available_days INTEGER,
                    hours_per_day REAL,
                    workflow_status TEXT,
                    state_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    agent TEXT,
                    action TEXT,
                    detail TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
                """
            )
            conn.commit()

    def create_session(self, meta: dict[str, Any], state: dict[str, Any]) -> str:
        session_id = meta.get("session_id") or str(uuid.uuid4())
        now = _utc()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    id, created_at, updated_at, user_goal, target_role,
                    experience_level, available_days, hours_per_day,
                    workflow_status, state_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    now,
                    now,
                    meta.get("user_goal"),
                    meta.get("target_role"),
                    meta.get("experience_level"),
                    meta.get("available_days"),
                    meta.get("hours_per_day"),
                    state.get("workflow_status", "initialized"),
                    json.dumps(state),
                ),
            )
            conn.commit()
        return session_id

    def save_state(self, session_id: str, state: dict[str, Any]) -> None:
        now = _utc()
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE sessions
                SET updated_at=?, workflow_status=?, target_role=?, state_json=?
                WHERE id=?
                """,
                (
                    now,
                    state.get("workflow_status"),
                    state.get("target_role"),
                    json.dumps(state),
                    session_id,
                ),
            )
            if cur.rowcount == 0:
                raise KeyError(f"Session not found: {session_id}")
            # Persist only the latest activity event to avoid duplicates on re-save.
            events = state.get("activity_log") or []
            if events:
                event = events[-1]
                existing = conn.execute(
                    """
                    SELECT id FROM event_log
                    WHERE session_id=? AND agent=? AND action=? AND detail=? AND created_at=?
                    LIMIT 1
                    """,
                    (
                        session_id,
                        event.get("agent"),
                        event.get("action"),
                        event.get("detail"),
                        event.get("timestamp") or now,
                    ),
                ).fetchone()
                if not existing:
                    conn.execute(
                        """
                        INSERT INTO event_log (session_id, created_at, agent, action, detail)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            event.get("timestamp") or now,
                            event.get("agent"),
                            event.get("action"),
                            event.get("detail"),
                        ),
                    )
            conn.commit()

    def get_state(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT state_json FROM sessions WHERE id=?", (session_id,)
            ).fetchone()
            if not row:
                return None
            return json.loads(row["state_json"])

    def list_events(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT created_at, agent, action, detail
                FROM event_log
                WHERE session_id=?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]


_store: SessionStore | None = None


def get_store() -> SessionStore:
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
