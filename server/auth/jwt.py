from datetime import datetime, timedelta, timezone

import jwt

from auth.config import JWT_EXPIRE_MINUTES, JWT_SECRET


def create_access_token(subject: str) -> tuple[str, int]:
    expires_in = JWT_EXPIRE_MINUTES * 60
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token, expires_in


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    sub = payload.get("sub")
    if not sub:
        raise jwt.InvalidTokenError("missing subject")
    return str(sub)
