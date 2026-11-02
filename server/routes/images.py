from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

import database
from auth.deps import get_current_user
from config import PUBLIC_IMAGE_URL_PREFIX, SLIDESHOW_URL_PREFIX

router = APIRouter()

_SLIDESHOW_LIMITS = {"day": 28, "week": 196, "month": 5880}


@router.get("/get_last_image/{offset}/{camera_id}")
def get_latest_image(
    camera_id: int, offset: int, _user: str = Depends(get_current_user)
):
    row = database.fetch_latest_capture(camera_id, offset)
    print("test")
    if not row:
        return "ERROR no db answer"

    dt_object = datetime.fromtimestamp(row["timestamp"])
    timestamp = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    ans = f"{PUBLIC_IMAGE_URL_PREFIX}/{row['path']}"
    print(ans)
    return JSONResponse(content={"url": ans, "timestamp": timestamp})


@router.get("/slideshow/{mode}/{camera_id}")
def slideshow(
    mode: str, camera_id: int, _user: str = Depends(get_current_user)
):
    if mode not in _SLIDESHOW_LIMITS:
        return JSONResponse(content={"error": "Invalid mode"}, status_code=400)

    rows = database.fetch_slideshow_captures(_SLIDESHOW_LIMITS[mode])
    if not rows:
        return "ERROR no db answer"

    data = []
    for row in rows:
        dt_object = datetime.fromtimestamp(row["timestamp"])
        timestamp = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        data.append(
            {"url": f"{SLIDESHOW_URL_PREFIX}/{row['path']}", "timestamp": timestamp}
        )

    print(rows)
    return JSONResponse(content={"images": data})


@router.get("/get_path")
async def get_path(
    camera_id: int, limit: int, _user: str = Depends(get_current_user)
):
    return database.fetch_capture_paths(camera_id, limit)
