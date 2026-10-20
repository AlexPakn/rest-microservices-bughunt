import secrets
import time
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="AuthService")
# Teaching fixtures only: use password hashes and persistent storage in production.
USERS = {
    "alice@example.com": {"password": "alice123", "id": 1},
    "bob@example.com": {"password": "bob123", "id": 2},
}
TOKEN_TTL_SECONDS = 3600
SESSIONS: dict[str, tuple[str, float]] = {}


def _now() -> float:
    return time.monotonic()


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResult(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user_id: int


class Identity(BaseModel):
    email: str
    user_id: int


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})


@app.post("/login", response_model=LoginResult)
async def login(payload: LoginRequest):
    user = USERS.get(payload.email)
    if not user or user["password"] != payload.password:
        raise unauthorized("Invalid credentials")
    now = _now()
    for old_token, (_, expires_at) in list(SESSIONS.items()):
        if expires_at <= now:
            del SESSIONS[old_token]
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = (payload.email, now + TOKEN_TTL_SECONDS)
    return LoginResult(access_token=token, expires_in=TOKEN_TTL_SECONDS, user_id=user["id"])


@app.get("/whoami", response_model=Identity)
async def whoami(authorization: str | None = Header(default=None)):
    scheme, separator, token = (authorization or "").partition(" ")
    if (scheme.lower() != "bearer" or not separator or not token
            or any(char.isspace() for char in token)):
        raise unauthorized("Missing or invalid token")
    session = SESSIONS.get(token)
    if session is None:
        raise unauthorized("Missing or invalid token")
    email, expires_at = session
    if expires_at <= _now() or email not in USERS:
        SESSIONS.pop(token, None)
        raise unauthorized("Missing or invalid token")
    return Identity(email=email, user_id=USERS[email]["id"])
