import sqlite3

from config import DB_PATH


def init_kasa_plugs_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS kasa_plugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            schedule_type TEXT NOT NULL CHECK (schedule_type IN ('simple', 'advanced')),
            schedule_json TEXT NOT NULL,
            schedule_enabled INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()
