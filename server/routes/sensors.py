from fastapi import APIRouter
from fastapi.responses import JSONResponse

import database

router = APIRouter()


@router.get("/get_TH/")
def get_th():
    row = database.fetch_latest_sensor_reading()
    if not row:
        return "ERROR no db answer"

    return JSONResponse(
        content={
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "battery": row["battery"],
            "timestamp": row["timestamp"],
        }
    )


@router.get("/get_THs")
def get_ths():
    return database.fetch_all_sensor_readings()
