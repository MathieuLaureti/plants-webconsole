import os
import time

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import PlainTextResponse

import database
from upload_storage import build_filename, make_dirs_for_today

router = APIRouter()


@router.post("/upload/{camera_id}", response_class=PlainTextResponse)
async def upload(camera_id: int, file: UploadFile = File(None), request: Request = None):
    save_dir = make_dirs_for_today(camera_id)
    filename = build_filename()
    path = os.path.join(save_dir, filename)

    data = await (file.read() if file else request.body())
    if not data:
        return PlainTextResponse("No data", status_code=400)

    with open(path, "wb") as f:
        f.write(data)

    size_bytes = len(data)
    timestamp = int(time.time())
    print(f"[+] Saved: {path} ({size_bytes} bytes)")

    database.insert_capture(
        filename=filename,
        timestamp=timestamp,
        path=path,
        size_bytes=size_bytes,
        camera_id=camera_id,
    )

    return "OK"
