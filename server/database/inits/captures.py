import sqlite3

from config import DB_PATH


def init_captures_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            path TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            analysis_status TEXT DEFAULT 'pending',
            result_json TEXT
        );
        """
    )
    conn.commit()
    conn.close()
