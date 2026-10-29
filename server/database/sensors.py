from typing import Any

import sqlite3

from config import DB_PATH
from database.connection import connect


def insert_sensor_reading(
    temperature: float,
    humidity: float,
    battery: int,
    timestamp: Any,
) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO sensor_data (temperature, humidity, battery, timestamp) VALUES (?, ?, ?, ?)
        """,
        (temperature, humidity, battery, timestamp),
    )
    conn.commit()
    conn.close()


def fetch_latest_sensor_reading() -> sqlite3.Row | None:
    conn = connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT temperature, humidity, battery, timestamp FROM sensor_data
        ORDER BY timestamp DESC LIMIT 1
        """
    )
    row = c.fetchone()
    conn.close()
    return row


def fetch_all_sensor_readings() -> list[sqlite3.Row]:
    conn = connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT temperature, humidity, battery, timestamp FROM sensor_data
        ORDER BY timestamp DESC
        """
    )
    rows = c.fetchall()
    conn.close()
    return rows
