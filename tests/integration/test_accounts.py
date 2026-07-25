"""API и сервис счетов + изоляция между пользователями."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.uuid_utils import new_uid
from app.database.models import Account, User, UserAccount
from app.dto.accounts import CreateAccountRequestDTO, UpdateAccountRequestDTO
from app.services.account_service import AccountService
from tests.conftest import make_manual_tx


def test_accounts_crud_api(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        "/v1/accounts",
        headers=auth_headers,
        json={"name": "Наличные", "balance": 5_000_00},
    )
    assert created.status_code == 200
    acc = created.json()["account"]
    assert acc["name"] == "Наличные"
    assert acc["balance"] == 5_000_00

    listed = client.get("/v1/accounts", headers=auth_headers)
    assert listed.status_code == 200
    ids = {a["id"] for a in listed.json()["accounts"]}
    assert acc["id"] in ids

    patched = client.patch(
        f"/v1/accounts/{acc['id']}",
        headers=auth_headers,
        json={"name": "Кошелёк"},
    )
    assert patched.status_code == 200
    assert patched.json()["account"]["name"] == "Кошелёк"

    deleted = client.delete(f"/v1/accounts/{acc['id']}", headers=auth_headers)
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True


def test_account_not_found_for_other_user(
    client: TestClient,
    db: Session,
    other_user: User,
    auth_headers: dict[str, str],
) -> None:
    alien = Account(uid=new_uid(), name="Чужой", balance=0)
    db.add(alien)
    db.flush()
    db.add(UserAccount(user_id=other_user.id, account_id=alien.id))
    db.commit()

    resp = client.get(f"/v1/accounts", headers=auth_headers)
    assert all(a["id"] != alien.uid for a in resp.json()["accounts"])

    assert (
        client.patch(
            f"/v1/accounts/{alien.uid}",
            headers=auth_headers,
            json={"name": "hack"},
        ).status_code
        == 404
    )
    assert client.delete(f"/v1/accounts/{alien.uid}", headers=auth_headers).status_code == 404


def test_create_account_service(db: Session, user: User) -> None:
    result = AccountService(db).create_account(
        user.id, CreateAccountRequestDTO(name="Сбер", balance=1_000_00)
    )
    assert result.account.balance == 1_000_00
    updated = AccountService(db).update_account(
        user.id, result.account.id, UpdateAccountRequestDTO(balance=2_000_00)
    )
    assert updated.account.balance == 2_000_00


def test_delete_empty_account(db: Session, user: User) -> None:
    created = AccountService(db).create_account(
        user.id, CreateAccountRequestDTO(name="Пустой", balance=0)
    )
    AccountService(db).delete_account(user.id, created.account.id)
    assert all(a.id != created.account.id for a in AccountService(db).list_accounts(user.id).accounts)


def test_delete_account_with_transactions_raises(
    db: Session, user: User, account: Account, system_categories
) -> None:
    """ORM не обнуляет account_id (NOT NULL) — удаление счёта с операциями падает."""
    from sqlalchemy.exc import IntegrityError

    make_manual_tx(
        db, user=user, account=account, amount=100_00, category=system_categories["other"]
    )
    with pytest.raises(IntegrityError):
        AccountService(db).delete_account(user.id, account.uid)
