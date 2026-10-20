import os

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="OrderService")
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8001")
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8002")
ORDERS: list[dict] = []


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    product_id: int = Field(alias="productId", gt=0)
    quantity: int = Field(alias="qty", gt=0)


async def authenticate(client, authorization):
    if not authorization:
        raise HTTPException(401, "Missing token", headers={"WWW-Authenticate": "Bearer"})
    response = await client.get(f"{AUTH_URL}/whoami", headers={"Authorization": authorization})
    if response.status_code in (401, 403):
        raise HTTPException(response.status_code, "Authorization rejected")
    return response.json()


@app.post("/orders")
async def create_order(payload: OrderRequest, authorization: str | None = Header(default=None)):
    async with httpx.AsyncClient() as client:
        identity = await authenticate(client, authorization)
        response = await client.get(f"{PRODUCT_URL}/products/{payload.product_id}")
        if response.status_code == 404:
            raise HTTPException(404, "Product not found")
        product = response.json()
        if payload.quantity > product["stock"]:
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
