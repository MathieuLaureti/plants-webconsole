import asyncio
from datetime import datetime

from bleak import BleakScanner

TARGET_MAC = "64:69:4E:9D:07:99"


async def get_ble_data():
    loop = asyncio.get_running_loop()
    future_data = loop.create_future()

    def callback(device, advertising_data):
        if device.address == TARGET_MAC and not future_data.done():
            payload = advertising_data.manufacturer_data
            future_data.set_result(payload)

    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()

    try:
        result = await asyncio.wait_for(future_data, timeout=10.0)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M")
        return (result, timestamp)
    except asyncio.TimeoutError:
        print("Timed out: Device not found.")
        return None
    finally:
        await scanner.stop()
