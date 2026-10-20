from fastapi import FastAPI, Response
from pydantic import BaseModel, ConfigDict, Field
from fastapi.responses import JSONResponse

app = FastAPI(title="AuthService")
USERS = {
    "alice@example.com": {"password": "alice123", "id": 1},
    "bob@example.com": {"password": "bob123", "id": 2},
}


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


@app.post("/login")
async def login(payload: LoginRequest):
    email, password = payload.email, payload.password
    user = USERS.get(email)
    if not user or user["password"] != password:
        return JSONResponse({"message": "invalid credentials"}, status_code=200)
    token = f"fake-token-for-{email}"
    return {"accessToken": token, "userId": user["id"]}


@app.get("/whoami")
async def whoami(authorization: str | None = None):
    if not authorization or not authorization.startswith("Bearer"):
        return JSONResponse({"error": "missing or invalid token"}, status_code=200)
    token = authorization.removeprefix("Bearer")
    email = token.replace("fake-token-for-", "")
    return {"email": email}
