import os
from datetime import datetime

from config import BASE_DIR


def ensure_upload_root() -> None:
    os.makedirs(BASE_DIR, exist_ok=True)


def make_dirs_for_today(camera_id: int) -> str:
    """Create subfolders: uploads/{camera_id}/YYYY-MM/DD and return that day's path."""
    now = datetime.now()
    camera_folder = os.path.join(BASE_DIR, str(camera_id))
    month_folder = os.path.join(camera_folder, now.strftime("%Y-%m"))
    day_folder = os.path.join(month_folder, now.strftime("%d"))
    os.makedirs(day_folder, exist_ok=True)
    return day_folder


def build_filename() -> str:
    """Return a readable filename like 2025-11-05_22-47.jpg"""
    return f"{datetime.now().strftime('%Y-%m-%d_%H:%M')}.jpg"
