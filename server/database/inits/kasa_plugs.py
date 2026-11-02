import sqlite3

from config import DB_PATH

_CREATE_SQL = """
CREATE TABLE kasa_plugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    schedule_type TEXT NOT NULL CHECK (schedule_type IN ('simple', 'advanced', 'static')),
    schedule_json TEXT NOT NULL,
    schedule_enabled INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
"""


def _migrate_schedule_type_check(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='kasa_plugs'"
    ).fetchone()
    if row is None or row[0] is None:
        return
    ddl = row[0]
    if "'static'" in ddl:
        return
    conn.execute("ALTER TABLE kasa_plugs RENAME TO kasa_plugs_old")
    conn.execute(_CREATE_SQL)
    conn.execute(
        """
        INSERT INTO kasa_plugs
            (id, host, title, description, schedule_type, schedule_json,
             schedule_enabled, created_at, updated_at)
        SELECT id, host, title, description, schedule_type, schedule_json,
               schedule_enabled, created_at, updated_at
        FROM kasa_plugs_old
        """
    )
    conn.execute("DROP TABLE kasa_plugs_old")


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
            schedule_type TEXT NOT NULL CHECK (schedule_type IN ('simple', 'advanced', 'static')),
            schedule_json TEXT NOT NULL,
            schedule_enabled INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );
        """
    )
    _migrate_schedule_type_check(conn)
    conn.commit()
    conn.close()
