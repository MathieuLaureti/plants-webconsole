import asyncio
from bleak import BleakScanner
import struct
import sqlite3
from datetime import datetime

TARGET_MAC = "64:69:4E:9D:07:99"

async def get_ble_data():
    #print(f"Listening for {TARGET_MAC}...")
    loop = asyncio.get_running_loop()
    future_data = loop.create_future()
    def callback(device, advertising_data):
        if device.address == TARGET_MAC and not future_data.done():
            payload = advertising_data.manufacturer_data
            future_data.set_result(payload)
    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()

    try:
        # 3. Wait here until callback calls set_result()
        # We add a timeout so the script doesn't hang forever if the device is offline
        result = await asyncio.wait_for(future_data, timeout=10.0)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M")
        return (result,timestamp)
        
    except asyncio.TimeoutError:
        print("Timed out: Device not found.")
        return None
        
    finally:
        # Always clean up the scanner
        await scanner.stop()

def decode_sensor_data(company_id, payload):
    """
    Decodes the 9-byte proprietary sensor data packet.
    Structure: [Temp LSB] [Temp MSB] [Hum LSB] [Hum MSB] [00] [Counter/Timer] [Batt] [CRC]
    Note: 'company_id' holds the Temp, 'payload' holds Hum, Batt, etc.
    """
    temp_bytes = struct.pack('<H', company_id)
    full_data = temp_bytes + payload

    if len(full_data) < 9:
        return None

    # --- Decode Core Values (Little Endian, Scale / 100) ---
    
    # Temperature (Bytes 0-1)
    # The bytes were packed as Little Endian, so we unpack them as an unsigned short (H)
    # Alternatively: temp_raw = full_data[0] | (full_data[1] << 8)
    temp_raw = struct.unpack('<H', full_data[0:2])[0]
    temperature_c = temp_raw / 100.0

    # Humidity (Bytes 2-3)
    hum_raw = struct.unpack('<H', full_data[2:4])[0]
    humidity_perc = hum_raw / 100.0

    # Battery (Byte 7)
    battery = full_data[7]
    
    # Internal Counter/Timer (Bytes 4-6, 8)
    #counter_hex = full_data[4:7].hex().upper()
    #checksum = full_data[8]

    return (temperature_c-0.50, humidity_perc-5, battery)

def data_handling(data):
    timestamp = data[1]
    data = data[0]
    line = list(data.items())[-1]
    sensor_values = decode_sensor_data(line[0], line[1])
    return (sensor_values[0],sensor_values[1],sensor_values[2],timestamp)

def write_to_db(data:tuple):
    MAX_ROWS = 500
    try:
        conn = sqlite3.connect("/home/mlaureti/plant_webconsole/server/database.db")
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                battery INTEGER NOT NULL,
                timestamp INTEGER NOT NULL
            );
        """)
        c.execute(f"""
            CREATE TRIGGER IF NOT EXISTS limit_table_size
            AFTER INSERT ON sensor_data
            WHEN (SELECT COUNT(*) FROM sensor_data) > {MAX_ROWS}
            BEGIN
                DELETE FROM sensor_data
                WHERE id NOT IN (
                    SELECT id FROM sensor_data ORDER BY id DESC LIMIT {MAX_ROWS}
                );
            END;
        """)
        c = conn.cursor()
        c.execute("""
            INSERT INTO sensor_data (temperature, humidity, battery, timestamp) VALUES (?, ?, ?, ?)
        """, (data[0], data[1], data[2], data[3]))
        conn.commit()
        conn.close()
        print("[+] Data written to database.")
    except Exception as e:
        print(f"Database error: {e}")
    
    
async def main():
    data = await get_ble_data()
    if not data[0] or data is None:
        print("No data received.")
    else:
        translated_data = data_handling(data)
        write_to_db(translated_data)
        print(translated_data)
        print("OK")

if __name__ == "__main__":
    asyncio.run(main())