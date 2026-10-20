import httpx

from conftest import issue_token


def test_three_services_login_catalog_order_and_owner_isolation(
    services, clients, monkeypatch
):
    """Actual ASGI apps communicate in memory; no mocked business responses."""
    original_client = httpx.AsyncClient

    class ServiceTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            app = (services.auth.app if request.url.port == 8001
                   else services.product.app)
            transport = httpx.ASGITransport(app=app)
            return await transport.handle_async_request(request)

    def client_factory(*args, **kwargs):
        kwargs["transport"] = ServiceTransport()
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    alice = {"Authorization": f"Bearer {issue_token(clients.auth)}"}
    bob = {"Authorization": f"Bearer {issue_token(clients.auth, 'bob@example.com', 'bob123')}"}
    product = clients.product.get("/products/100").json()
    response = clients.order.post("/orders", headers=alice,
                                   json={"productId": product["product_id"], "qty": 1})
    assert response.status_code == 201
    assert response.json()["user_id"] == 1
    assert clients.order.get("/orders", headers=bob).json() == {"orders": []}
    assert len(clients.order.get("/orders", headers=alice).json()["orders"]) == 1
