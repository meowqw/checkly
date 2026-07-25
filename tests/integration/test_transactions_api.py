"""API транзакций: CRUD, detail, изоляция, comment update."""
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import Currency, TransactionType
from app.core.exceptions import NotFoundError
from app.database.models import Account, Category, User
from app.dto.transactions import CreateManualTransactionDTO
from app.services.transaction_service import TransactionService
from tests.conftest import make_manual_tx, make_qr_tx
import pytest


def test_transactions_api_crud(
    client: TestClient,
    account: Account,
    system_categories: dict[str, Category],
    auth_headers: dict[str, str],
) -> None:
    created = client.post(
        "/v1/transactions",
        headers=auth_headers,
        json={
            "account_id": account.uid,
            "type": "expense",
            "amount": 750_00,
            "currency": "RUB",
            "occurred_at": "2026-06-15T14:00:00",
            "category_id": system_categories["dairy"].uid,
            "comment": "Молоко",
        },
    )
    assert created.status_code == 200
    tx_id = created.json()["transaction"]["id"]

    detail = client.get(f"/v1/transactions/{tx_id}", headers=auth_headers)
    assert detail.status_code == 200
    body = detail.json()["transaction"]
    assert body["amount"] == 750_00
    assert body["source"] == "manual"
    assert body["items"]

    patched = client.patch(
        f"/v1/transactions/{tx_id}",
        headers=auth_headers,
        json={"comment": "Молоко 2", "amount": 800_00},
    )
    assert patched.status_code == 200
    assert patched.json()["transaction"]["comment"] == "Молоко 2"

    deleted = client.delete(f"/v1/transactions/{tx_id}", headers=auth_headers)
    assert deleted.status_code == 200
    assert client.get(f"/v1/transactions/{tx_id}", headers=auth_headers).status_code == 404


def test_cannot_access_other_user_transaction(
    client: TestClient,
    db: Session,
    user: User,
    other_user: User,
    account: Account,
    system_categories: dict[str, Category],
    auth_headers: dict[str, str],
) -> None:
    # счёт и tx принадлежат user; логинимся как other через его токен
    from app.core.security import create_access_token
    from app.core.uuid_utils import new_uid
    from app.database.models import UserAccount

    other_acc = Account(uid=new_uid(), name="Other", balance=0)
    db.add(other_acc)
    db.flush()
    db.add(UserAccount(user_id=other_user.id, account_id=other_acc.id, role="owner"))
    db.commit()

    tx = make_manual_tx(
        db, user=user, account=account, amount=100_00, category=system_categories["other"]
    )
    other_headers = {
        "Authorization": f"Bearer {create_access_token(other_user.uid)}",
        "X-Timezone": "Europe/Moscow",
    }
    assert client.get(f"/v1/transactions/{tx.uid}", headers=other_headers).status_code == 404
    assert (
        client.patch(
            f"/v1/transactions/{tx.uid}",
            headers=other_headers,
            json={"comment": "x"},
        ).status_code
        == 404
    )


def test_api_forbid_patch_qr(
    client: TestClient,
    db: Session,
    user: User,
    account: Account,
    system_categories: dict[str, Category],
    auth_headers: dict[str, str],
) -> None:
    qr = make_qr_tx(
        db,
        user=user,
        account=account,
        items=[("X", 100_00, system_categories["other"])],
    )
    resp = client.patch(
        f"/v1/transactions/{qr.uid}",
        headers=auth_headers,
        json={"amount": 50_00},
    )
    assert resp.status_code == 403


def test_create_unknown_account_raises(
    db: Session, user: User, system_categories: dict[str, Category]
) -> None:
    with pytest.raises(NotFoundError):
        TransactionService(db).create_manual_transaction(
            CreateManualTransactionDTO(
                user_id=user.id,
                account_uid="00000000-0000-0000-0000-000000000099",
                type=TransactionType.EXPENSE,
                amount=100_00,
                currency=Currency.RUB,
                occurred_at=datetime(2026, 6, 1, 12, 0, 0),
                category_uid=system_categories["other"].uid,
                timezone="Europe/Moscow",
            )
        )
