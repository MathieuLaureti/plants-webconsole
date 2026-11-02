import os

KASA_USERNAME = os.environ.get("KASA_USERNAME", "")
KASA_PASSWORD = os.environ.get("KASA_PASSWORD", "")


def is_configured() -> bool:
    return bool(KASA_USERNAME and KASA_PASSWORD)
