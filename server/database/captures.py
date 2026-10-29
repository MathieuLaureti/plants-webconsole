import sqlite3

from config import DB_PATH
from database.connection import connect


def insert_capture(
    *,
    filename: str,
    timestamp: int,
    path: str,
    size_bytes: int,
    camera_id: int,
) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO captures (filename, timestamp, path, size_bytes, camera_id) VALUES (?, ?, ?, ?, ?)",
        (filename, timestamp, path, size_bytes, camera_id),
    )
    conn.commit()
    conn.close()


def fetch_latest_capture(camera_id: int, offset: int) -> sqlite3.Row | None:
    conn = connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT path, timestamp FROM captures
        WHERE camera_id = ?
        ORDER BY timestamp DESC LIMIT 1 OFFSET ?
        """,
        (camera_id, offset),
    )
    row = c.fetchone()
    conn.close()
    return row


def fetch_slideshow_captures(limit: int) -> list[sqlite3.Row]:
    conn = connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT path, timestamp FROM captures ORDER BY timestamp ASC LIMIT ?
        """,
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def fetch_capture_paths(camera_id: int, limit: int) -> list[sqlite3.Row]:
    conn = connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT path FROM captures
        WHERE camera_id = ?
        ORDER BY timestamp DESC LIMIT ?
        """,
        (camera_id, limit),
    )
    rows = c.fetchall()
    conn.close()
    return rows
