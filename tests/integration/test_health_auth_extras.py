"""Health, timezone sync, auth register duplicate login."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import User


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert "x-process-time-ms" in resp.headers


def test_login_updates_timezone(
    client: TestClient, db: Session, user: User
) -> None:
    resp = client.post(
        "/v1/auth/login",
        json={"login": "demo", "password": "secret123"},
        headers={"X-Timezone": "Asia/Tomsk"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["timezone"] == "Asia/Tomsk"
    db.refresh(user)
    assert user.timezone == "Asia/Tomsk"


def test_register_duplicate_login(client: TestClient) -> None:
    payload = {"email": "a1@example.com", "login": "samelogin", "password": "secret123"}
    assert client.post("/v1/auth/register", json=payload).status_code == 200
    again = client.post(
        "/v1/auth/register",
        json={"email": "a2@example.com", "login": "samelogin", "password": "secret123"},
    )
    assert again.status_code == 409


def test_authorized_request_syncs_timezone_header(
    client: TestClient, db: Session, user: User, auth_headers: dict[str, str]
) -> None:
    # UserTimezone есть на /transactions и /stats, не на /accounts
    headers = {**auth_headers, "X-Timezone": "Europe/Kaliningrad"}
    resp = client.get("/v1/transactions", headers=headers)
    assert resp.status_code == 200
    db.refresh(user)
    assert user.timezone == "Europe/Kaliningrad"
