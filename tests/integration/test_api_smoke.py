"""API smoke: пагинация в JSON-ответе."""
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Account, Category, User
from tests.conftest import make_manual_tx


def test_transactions_api_pagination(
    client: TestClient,
    db: Session,
    user: User,
    account: Account,
    system_categories: dict[str, Category],
    auth_headers: dict[str, str],
) -> None:
    for i in range(3):
        make_manual_tx(
            db,
            user=user,
            account=account,
            amount=100_00,
            category=system_categories["other"],
            occurred_at=datetime(2026, 6, 1 + i, 12, 0, 0),
            comment=f"api-{i}",
        )

    full = client.get(
        "/v1/transactions",
        params={"from": "2026-06-01", "to": "2026-06-30"},
        headers=auth_headers,
    )
    assert full.status_code == 200
    body = full.json()
    assert len(body["transactions"]) == 3
    assert "total" not in body

    page = client.get(
        "/v1/transactions",
        params={"from": "2026-06-01", "to": "2026-06-30", "limit": 2, "offset": 0},
        headers=auth_headers,
    )
    assert page.status_code == 200
    data = page.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["has_more"] is True
    assert len(data["transactions"]) == 2


def test_stats_api(
    client: TestClient,
    db: Session,
    user: User,
    account: Account,
    system_categories: dict[str, Category],
    auth_headers: dict[str, str],
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=250_00,
        category=system_categories["dairy"],
        occurred_at=datetime(2026, 6, 10, 12, 0, 0),
    )
    resp = client.get(
        "/v1/stats",
        params={"from": "2026-06-01", "to": "2026-06-30"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["expense"] == 250_00
    assert data["income"] == 0
    assert data["categories"]
