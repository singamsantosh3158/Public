"""SQLite persistence for conversations. Stdlib only — no new dependency.

Each call opens a short-lived connection; fine for a local single-user app
and avoids cross-thread sqlite3 connection-sharing issues under FastAPI's
threadpool-per-sync-request model.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "audit_chat.db")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            history TEXT NOT NULL,
            agent_items TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def load_all() -> dict[str, dict]:
    """Returns {conv_id: {"title", "history", "agent_items"}}, newest-updated first."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, title, history, agent_items FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        return {
            row[0]: {"title": row[1], "history": json.loads(row[2]), "agent_items": json.loads(row[3])}
            for row in rows
        }
    finally:
        conn.close()


def save(conv_id: str, title: str | None, history: list, agent_items: list) -> None:
    conn = _connect()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO conversations (id, title, history, agent_items, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                history=excluded.history,
                agent_items=excluded.agent_items,
                updated_at=excluded.updated_at
            """,
            (conv_id, title, json.dumps(history, default=str), json.dumps(agent_items, default=str), now, now),
        )
        conn.commit()
    finally:
        conn.close()


def rename(conv_id: str, title: str) -> None:
    conn = _connect()
    try:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.now(timezone.utc).isoformat(), conv_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete(conv_id: str) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
    finally:
        conn.close()
