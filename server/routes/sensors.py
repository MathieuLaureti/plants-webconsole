from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

import database
from auth.deps import get_current_user

router = APIRouter()


@router.get("/get_TH/")
def get_th(_user: str = Depends(get_current_user)):
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
def get_ths(_user: str = Depends(get_current_user)):
    return database.fetch_all_sensor_readings()
