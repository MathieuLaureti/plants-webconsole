import os
import subprocess
import tempfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

import database
from config import CODE_ROOT

router = APIRouter()


@router.get("/generate-timelapse/{camera_id}/{limit}")
async def generate_timelapse(camera_id: int, limit: int):
    image_paths = database.fetch_capture_paths(camera_id, limit)
    if not image_paths:
        raise HTTPException(status_code=404, detail="No images found")

    output_fd, output_video_path = tempfile.mkstemp(suffix=".mp4")
    os.close(output_fd)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_list_path = os.path.join(tmpdir, "images.txt")

            with open(input_list_path, "w") as f:
                for row in reversed(image_paths):
                    path = row["path"]
                    if not path.startswith("/"):
                        path = os.path.abspath(os.path.join(CODE_ROOT, path))

                    if os.path.exists(path):
                        f.write(f"file '{path}'\n")
                        f.write("duration 0.1\n")

            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                input_list_path,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-movflags",
                "faststart",
                output_video_path,
            ]

            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode != 0:
                print(process.stderr)
                raise HTTPException(status_code=500, detail="Video encoding failed")

        return FileResponse(
            output_video_path,
            media_type="video/mp4",
            background=BackgroundTask(lambda: os.remove(output_video_path)),
        )
    except Exception:
        if os.path.exists(output_video_path):
            os.remove(output_video_path)
        raise
