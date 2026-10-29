import os

JWT_SECRET = os.environ.get("JWT_SECRET", "")
CONSOLE_USERNAME = os.environ.get("CONSOLE_USERNAME", "")
CONSOLE_PASSWORD = os.environ.get("CONSOLE_PASSWORD", "")
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "720"))

_DEFAULT_UPLOAD_CIDRS = "192.168.0.0/16,10.0.0.0/8,172.16.0.0/12"
UPLOAD_ALLOWED_CIDRS = os.environ.get("UPLOAD_ALLOWED_CIDRS", _DEFAULT_UPLOAD_CIDRS)
UPLOAD_FORBIDDEN_CLIENT_IPS = os.environ.get("UPLOAD_FORBIDDEN_CLIENT_IPS", "192.168.2.99")
PUBLIC_API_HOSTS = os.environ.get("PUBLIC_API_HOSTS", "homelabdu204.ca")


def auth_is_configured() -> bool:
    return bool(JWT_SECRET and CONSOLE_USERNAME and CONSOLE_PASSWORD)


def validate_auth_config() -> None:
    if not auth_is_configured():
        raise RuntimeError(
            "JWT auth requires JWT_SECRET, CONSOLE_USERNAME, and CONSOLE_PASSWORD in the environment"
        )
