"""API: регистрация и логин."""
from fastapi.testclient import TestClient


def test_register_and_login(client: TestClient) -> None:
    reg = client.post(
        "/v1/auth/register",
        json={"email": "new@example.com", "login": "newbie", "password": "secret123"},
        headers={"X-Timezone": "Europe/Moscow"},
    )
    assert reg.status_code == 200
    body = reg.json()
    assert body["user"]["login"] == "newbie"
    assert body["access_token"]

    login = client.post(
        "/v1/auth/login",
        json={"login": "newbie", "password": "secret123"},
        headers={"X-Timezone": "Europe/Moscow"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["id"] == body["user"]["id"]


def test_register_duplicate_email(client: TestClient) -> None:
    payload = {"email": "dup@example.com", "login": "dup1", "password": "secret123"}
    assert client.post("/v1/auth/register", json=payload).status_code == 200
    again = client.post(
        "/v1/auth/register",
        json={"email": "dup@example.com", "login": "dup2", "password": "secret123"},
    )
    assert again.status_code == 409


def test_login_bad_password(client: TestClient) -> None:
    client.post(
        "/v1/auth/register",
        json={"email": "u@example.com", "login": "user1", "password": "secret123"},
    )
    resp = client.post(
        "/v1/auth/login",
        json={"login": "user1", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_protected_without_token(client: TestClient) -> None:
    resp = client.get("/v1/accounts")
    assert resp.status_code == 401
