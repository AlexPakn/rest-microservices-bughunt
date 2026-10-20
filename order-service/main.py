import os

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="OrderService")
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8001").rstrip("/")
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8002").rstrip("/")
UPSTREAM_TIMEOUT_SECONDS = 5.0
ORDERS: list[dict] = []


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    product_id: int = Field(alias="productId", gt=0)
    quantity: int = Field(alias="qty", gt=0)


class Identity(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    user_id: int = Field(gt=0)
    email: str = Field(min_length=1)


class ProductSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    product_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    price: float = Field(ge=0, allow_inf_nan=False)
    stock: int = Field(ge=0)


async def upstream(client, url, model, service, *, headers=None, allowed_errors=()):
    try:
        response = await client.get(url, headers=headers)
    except httpx.TimeoutException:
        raise HTTPException(504, f"{service} timed out") from None
    except httpx.RequestError:
        raise HTTPException(502, f"{service} unavailable") from None
    if response.status_code in allowed_errors:
        detail = "Authorization rejected" if service == "Auth service" else "Product not found"
        challenge = {"WWW-Authenticate": "Bearer"} if response.status_code == 401 else None
        raise HTTPException(response.status_code, detail, headers=challenge)
    if response.status_code != 200:
        raise HTTPException(502, f"{service} returned an unexpected status")
    try:
        return model.model_validate(response.json())
    except ValueError:
        raise HTTPException(502, f"{service} returned an invalid response") from None


async def authenticate(client, authorization):
    if not authorization:
        raise HTTPException(401, "Missing token", headers={"WWW-Authenticate": "Bearer"})
    return await upstream(client, f"{AUTH_URL}/whoami", Identity, "Auth service",
                          headers={"Authorization": authorization}, allowed_errors=(401, 403))


@app.post("/orders")
async def create_order(payload: OrderRequest, authorization: str | None = Header(default=None)):
    async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT_SECONDS, follow_redirects=False) as client:
        identity = await authenticate(client, authorization)
        product = await upstream(client, f"{PRODUCT_URL}/products/{payload.product_id}",
                                 ProductSnapshot, "Product service", allowed_errors=(404,))
        if product.product_id != payload.product_id:
            raise HTTPException(502, "Product service returned the wrong product")
        if payload.quantity > product.stock:
            raise HTTPException(409, "Insufficient stock")
    order = {
        "order_id": len(ORDERS) + 1,
        "product_id": payload.product_id,
        "quantity": payload.quantity,
        "status": "created",
    }
    ORDERS.append(order)
    return JSONResponse(order, status_code=201)


@app.get("/orders")
async def list_orders():
    return {"orders": ORDERS}
