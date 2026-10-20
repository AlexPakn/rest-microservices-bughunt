from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="AuthService")
USERS = {
    "alice@example.com": {"password": "alice123", "id": 1},
    "bob@example.com": {"password": "bob123", "id": 2},
}


@app.get("/login")
async def login(email: str, password: str, response: Response):
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
