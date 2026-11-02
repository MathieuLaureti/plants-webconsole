import os

KASA_HOST = os.environ.get("KASA_HOST", "")
KASA_USERNAME = os.environ.get("KASA_USERNAME", "")
KASA_PASSWORD = os.environ.get("KASA_PASSWORD", "")


def is_configured() -> bool:
    return bool(KASA_HOST and KASA_USERNAME and KASA_PASSWORD)
