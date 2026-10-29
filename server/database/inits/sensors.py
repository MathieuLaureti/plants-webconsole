import sqlite3

from config import DB_PATH


def init_sensor_db(max_rows: int = 500) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            battery INTEGER NOT NULL,
            timestamp INTEGER NOT NULL
        );
        """
    )
    c.execute(
        f"""
        CREATE TRIGGER IF NOT EXISTS limit_table_size
        AFTER INSERT ON sensor_data
        WHEN (SELECT COUNT(*) FROM sensor_data) > {max_rows}
        BEGIN
            DELETE FROM sensor_data
            WHERE id NOT IN (
                SELECT id FROM sensor_data ORDER BY id DESC LIMIT {max_rows}
            );
        END;
        """
    )
    conn.commit()
    conn.close()
