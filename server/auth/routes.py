from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from auth.config import CONSOLE_PASSWORD, CONSOLE_USERNAME
from auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
def login(body: LoginBody) -> TokenResponse:
    if body.username != CONSOLE_USERNAME or body.password != CONSOLE_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token, expires_in = create_access_token(body.username)
    return TokenResponse(access_token=token, expires_in=expires_in)
