import asyncio

import database
from sensor_scan.ble import get_ble_data
from sensor_scan.decode import data_handling


def write_to_db(data: tuple) -> None:
    try:
        database.init_sensor_db()
        database.insert_sensor_reading(data[0], data[1], data[2], data[3])
        print("[+] Data written to database.")
    except Exception as e:
        print(f"Database error: {e}")


async def main():
    data = await get_ble_data()
    if data is None or not data[0]:
        print("No data received.")
        return

    translated_data = data_handling(data)
    write_to_db(translated_data)
    print(translated_data)
    print("OK")
