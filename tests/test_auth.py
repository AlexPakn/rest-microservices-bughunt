import pytest

from conftest import issue_token


def test_b01_login_accepts_json_post(clients):
    response = clients.auth.post("/login", json={
        "email": "alice@example.com", "password": "alice123"
    })
    assert response.status_code == 200


def test_b01_login_does_not_accept_password_in_url(clients):
    response = clients.auth.get("/login", params={
        "email": "alice@example.com", "password": "alice123"
    })
    assert response.status_code == 405


def test_b02_bad_credentials_are_unauthorized(clients):
    is_post = any(route.path == "/login" and "POST" in getattr(route, "methods", set())
                  for route in clients.auth.app.routes)
    credentials = {"email": "alice@example.com", "password": "wrong"}
    response = (clients.auth.post("/login", json=credentials) if is_post
                else clients.auth.get("/login", params=credentials))
    assert response.status_code == 401


def test_b03_whoami_reads_authorization_header(clients, token):
    response = clients.auth.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert response.json().get("email") == "alice@example.com"


def test_b03_query_cannot_replace_authorization_header(clients, token):
    response = clients.auth.get("/whoami", params={"authorization": f"Bearer {token}"})
    assert "email" not in response.json()


def test_b04_missing_token_returns_401(clients):
    response = clients.auth.get("/whoami")
    assert response.status_code == 401


def test_b04_unauthorized_response_has_bearer_challenge(clients):
    assert clients.auth.get("/whoami").headers.get("www-authenticate") == "Bearer"


@pytest.mark.parametrize("authorization", [
    "Bearer fake-token-for-alice@example.com",
    "Bearer fake-token-for-admin@example.com",
    "Bearernonsense", "Bearer", "Basic abc", "Bearer a b",
])
def test_b05_unissued_or_malformed_token_rejected(clients, authorization):
    # Supply both to reach the original buggy token parser independently of B03.
    response = clients.auth.get("/whoami", headers={"Authorization": authorization},
                                params={"authorization": authorization})
    assert response.status_code == 401


def test_b05_expired_token_rejected(clients, services, monkeypatch):
    monkeypatch.setattr(services.auth, "_now", lambda: 100.0, raising=False)
    token = issue_token(clients.auth)
    monkeypatch.setattr(services.auth, "_now", lambda: 10000.0)
    authorization = f"Bearer {token}"
    response = clients.auth.get("/whoami", headers={"Authorization": authorization},
                                params={"authorization": authorization})
    assert response.status_code == 401


def test_valid_login_and_identity(clients, token):
    response = clients.auth.get("/whoami", headers={"Authorization": f"bearer {token}"})
    assert response.json() == {"email": "alice@example.com", "user_id": 1}
