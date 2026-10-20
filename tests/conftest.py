import importlib.util
import sys
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def services():
    modules = {}
    for name in ("auth", "product", "order"):
        module_name = f"test_service_{name}"
        spec = importlib.util.spec_from_file_location(
            module_name, ROOT / f"{name}-service" / "main.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        modules[name] = module
    yield SimpleNamespace(**modules)
    for name in modules:
        sys.modules.pop(f"test_service_{name}", None)


@pytest.fixture
def clients(services):
    with ExitStack() as stack:
        yield SimpleNamespace(**{
            name: stack.enter_context(TestClient(getattr(services, name).app))
            for name in ("auth", "product", "order")
        })


def issue_token(client, email="alice@example.com", password="alice123"):
    # Supports both revisions so each regression test targets its own defect.
    if any(route.path == "/login" and "POST" in getattr(route, "methods", set())
           for route in client.app.routes):
        response = client.post("/login", json={"email": email, "password": password})
    else:
        response = client.get("/login", params={"email": email, "password": password})
    body = response.json()
    return body.get("access_token", body.get("accessToken"))


@pytest.fixture
def token(clients):
    return issue_token(clients.auth)


@pytest.fixture
def downstream(monkeypatch):
    original_client = httpx.AsyncClient
    state = SimpleNamespace(
        auth_status=200,
        auth_body={"email": "alice@example.com", "user_id": 1},
        product_status=200,
        product_body={"product_id": 100, "name": "Keyboard", "price": 59.99, "stock": 5},
        fail_service=None,
        error=None,
        raw_body=None,
        calls=[],
    )

    def respond(request):
        state.calls.append(request)
        service = "auth" if request.url.path == "/whoami" else "product"
        if service == state.fail_service:
            raise state.error("simulated upstream failure", request=request)
        if state.raw_body is not None and service == "product":
            return httpx.Response(200, content=state.raw_body)
        return httpx.Response(
            getattr(state, f"{service}_status"),
            json=getattr(state, f"{service}_body"),
        )

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(respond)
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    return state
