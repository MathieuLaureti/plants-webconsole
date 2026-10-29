import struct


def decode_sensor_data(company_id: int, payload: bytes):
    """
    Decodes the 9-byte proprietary sensor data packet.
    Structure: [Temp LSB] [Temp MSB] [Hum LSB] [Hum MSB] [00] [Counter/Timer] [Batt] [CRC]
    """
    temp_bytes = struct.pack("<H", company_id)
    full_data = temp_bytes + payload

    if len(full_data) < 9:
        return None

    temp_raw = struct.unpack("<H", full_data[0:2])[0]
    temperature_c = temp_raw / 100.0

    hum_raw = struct.unpack("<H", full_data[2:4])[0]
    humidity_perc = hum_raw / 100.0

    battery = full_data[7]

    return (temperature_c - 0.50, humidity_perc - 5, battery)


def data_handling(data):
    timestamp = data[1]
    payload_map = data[0]
    line = list(payload_map.items())[-1]
    sensor_values = decode_sensor_data(line[0], line[1])
    return (sensor_values[0], sensor_values[1], sensor_values[2], timestamp)
