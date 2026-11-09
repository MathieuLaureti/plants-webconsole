import json
import sqlite3
import time
from typing import Any

from database.connection import connect


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "host": row["host"],
        "title": row["title"],
        "description": row["description"],
        "schedule_type": row["schedule_type"],
        "schedule": json.loads(row["schedule_json"]),
        "schedule_enabled": bool(row["schedule_enabled"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_plugs() -> list[dict[str, Any]]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM kasa_plugs ORDER BY title COLLATE NOCASE, id"
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def fetch_plug(plug_id: int) -> dict[str, Any] | None:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM kasa_plugs WHERE id = ?", (plug_id,)).fetchone()
        if row is None:
            return None
        return _row_to_dict(row)
    finally:
        conn.close()


def fetch_enabled_plugs() -> list[dict[str, Any]]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM kasa_plugs WHERE schedule_enabled = 1 ORDER BY id"
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def insert_plug(
    *,
    host: str,
    title: str,
    description: str | None,
    schedule_type: str,
    schedule: dict[str, Any],
) -> dict[str, Any]:
    now = int(time.time())
    conn = connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO kasa_plugs
                (host, title, description, schedule_type, schedule_json,
                 schedule_enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                host.strip(),
                title.strip(),
                description,
                schedule_type,
                json.dumps(schedule),
                now,
                now,
            ),
        )
        conn.commit()
        plug_id = cur.lastrowid
    finally:
        conn.close()
    return fetch_plug(int(plug_id))  # type: ignore[arg-type]


def update_plug(
    plug_id: int,
    *,
    host: str | None = None,
    title: str | None = None,
    description: str | None = None,
    schedule_type: str | None = None,
    schedule: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    existing = fetch_plug(plug_id)
    if existing is None:
        return None
    now = int(time.time())
    conn = connect()
    try:
        conn.execute(
            """
            UPDATE kasa_plugs SET
                host = ?,
                title = ?,
                description = ?,
                schedule_type = ?,
                schedule_json = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                (host or existing["host"]).strip(),
                (title or existing["title"]).strip(),
                description if description is not None else existing["description"],
                schedule_type or existing["schedule_type"],
                json.dumps(schedule if schedule is not None else existing["schedule"]),
                now,
                plug_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return fetch_plug(plug_id)


def set_schedule_enabled(plug_id: int, enabled: bool) -> dict[str, Any] | None:
    existing = fetch_plug(plug_id)
    if existing is None:
        return None
    now = int(time.time())
    conn = connect()
    try:
        conn.execute(
            "UPDATE kasa_plugs SET schedule_enabled = ?, updated_at = ? WHERE id = ?",
            (1 if enabled else 0, now, plug_id),
        )
        conn.commit()
    finally:
        conn.close()
    return fetch_plug(plug_id)


def delete_plug(plug_id: int) -> bool:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM kasa_plugs WHERE id = ?", (plug_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
