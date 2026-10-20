import httpx
import pytest

HEADERS = {"Authorization": "Bearer test-session"}
VALID = {"productId": 100, "qty": 2}


def create(clients, payload=None, headers=None):
    return clients.order.post("/orders", json=VALID if payload is None else payload,
                              headers=HEADERS if headers is None else headers)


def test_b08_order_requires_authorization(clients, downstream, services):
    response = create(clients, headers={})
    assert response.status_code == 401
    assert services.order.ORDERS == []


@pytest.mark.parametrize("status", [401, 403])
def test_b08_order_honors_auth_rejection(clients, downstream, services, status):
    downstream.auth_status = status
    response = create(clients)
    assert response.status_code == status
    assert services.order.ORDERS == []


@pytest.mark.parametrize("payload", [
    {}, {"productId": 100}, {"productId": 100, "qty": 0},
    {"productId": 100, "qty": -1}, {"productId": 100, "qty": 1.5},
    {"productId": 100, "qty": True}, {"productId": 100, "qty": "2"},
    {"productId": "100", "qty": 1}, {"productId": -1, "qty": 1},
    {"productId": True, "qty": 1}, {"productId": 100, "qty": None},
    {"productId": 100, "qty": 1, "status": "paid"},
])
def test_b09_invalid_order_payload_rejected(clients, downstream, services, payload):
    response = create(clients, payload)
    assert response.status_code == 422
    assert services.order.ORDERS == []


def test_b10_unknown_product_cannot_be_ordered(clients, downstream, services):
    downstream.product_status = 404
    downstream.product_body = {"detail": "Product not found"}
    response = create(clients, {"productId": 9999, "qty": 1})
    assert response.status_code == 404
    assert services.order.ORDERS == []


@pytest.mark.parametrize("stock,qty", [(0, 1), (5, 6)])
def test_b11_insufficient_stock_rejected(clients, downstream, services, stock, qty):
    downstream.product_body["stock"] = stock
    response = create(clients, {"productId": 100, "qty": qty})
    assert response.status_code == 409
    assert services.order.ORDERS == []


@pytest.mark.parametrize("service", ["auth", "product"])
@pytest.mark.parametrize("error,expected", [(httpx.ConnectError, 502),
                                             (httpx.ReadTimeout, 504)])
def test_b12_dependency_transport_failure_is_explicit(
    clients, downstream, services, service, error, expected
):
    downstream.fail_service, downstream.error = service, error
    response = create(clients)
    assert response.status_code == expected
    assert services.order.ORDERS == []


@pytest.mark.parametrize("service", ["auth", "product"])
@pytest.mark.parametrize("status", [200, 302, 500])
def test_b12_invalid_dependency_response_fails_closed(
    clients, downstream, services, service, status
):
    setattr(downstream, f"{service}_status", status)
    setattr(downstream, f"{service}_body", {"unexpected": "shape"})
    response = create(clients)
    assert response.status_code == 502
    assert services.order.ORDERS == []


def test_b12_non_json_dependency_response_rejected(clients, downstream, services):
    downstream.raw_body = b"not json"
    response = create(clients)
    assert response.status_code == 502
    assert services.order.ORDERS == []


def test_b12_wrong_product_identity_rejected(clients, downstream, services):
    downstream.product_body["product_id"] = 101
    response = create(clients)
    assert response.status_code == 502
    assert services.order.ORDERS == []


def test_b13_order_list_requires_authentication(clients, downstream):
    assert clients.order.get("/orders").status_code == 401


def test_b13_users_only_see_their_own_orders(clients, downstream, services):
    services.order.ORDERS.extend([
        {"order_id": 1, "user_id": 1, "product_id": 100, "quantity": 1, "status": "created"},
        {"order_id": 2, "user_id": 2, "product_id": 100, "quantity": 1, "status": "created"},
    ])
    response = clients.order.get("/orders", headers=HEADERS)
    assert [order["order_id"] for order in response.json()["orders"]] == [1]


def test_b13_created_order_belongs_to_authenticated_user(clients, downstream):
    response = create(clients)
    assert response.json().get("user_id") == 1


def test_valid_order_created(clients, downstream):
    response = create(clients)
    assert response.status_code == 201
    assert response.json()["quantity"] == 2


def test_b11_exact_stock_quantity_is_allowed(clients, downstream):
    assert create(clients, {"productId": 100, "qty": 5}).status_code == 201
