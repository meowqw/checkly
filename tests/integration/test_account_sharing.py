"""Семейный доступ: invite / join / shared transactions."""
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import AccountMemberRole
from app.database.models import Account, Category, User
from tests.conftest import make_manual_tx


def test_invite_join_and_shared_access(
    client: TestClient,
    db: Session,
    user: User,
    other_user: User,
    account: Account,
    system_categories: dict[str, Category],
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
) -> None:
    tx = make_manual_tx(
        db,
        user=user,
        account=account,
        amount=250_00,
        category=system_categories["other"],
        occurred_at=datetime(2026, 6, 15, 12, 0, 0),
    )

    invite = client.post(f"/v1/accounts/{account.uid}/invites", headers=auth_headers)
    assert invite.status_code == 200
    token = invite.json()["token"]
    assert token

    joined = client.post(
        "/v1/accounts/join",
        headers=other_auth_headers,
        json={"token": token},
    )
    assert joined.status_code == 200
    body = joined.json()["account"]
    assert body["id"] == account.uid
    member_ids = {m["id"] for m in body["members"]}
    assert user.uid in member_ids
    assert other_user.uid in member_ids
    roles = {m["id"]: m["role"] for m in body["members"]}
    assert roles[user.uid] == AccountMemberRole.OWNER.value
    assert roles[other_user.uid] == AccountMemberRole.MEMBER.value

    listed = client.get("/v1/accounts", headers=other_auth_headers)
    assert listed.status_code == 200
    assert any(a["id"] == account.uid for a in listed.json()["accounts"])

    txs = client.get(
        "/v1/transactions",
        headers=other_auth_headers,
        params={"from": "2026-06-01", "to": "2026-06-30"},
    )
    assert txs.status_code == 200
    assert any(t["id"] == tx.uid for t in txs.json()["transactions"])

    detail = client.get(f"/v1/transactions/{tx.uid}", headers=other_auth_headers)
    assert detail.status_code == 200

    stats = client.get(
        "/v1/stats",
        headers=other_auth_headers,
        params={"from": "2026-06-01", "to": "2026-06-30", "account_id": account.uid},
    )
    assert stats.status_code == 200
    assert stats.json()["expense"] == 250_00

    # одноразовый токен
    reuse = client.post(
        "/v1/accounts/join",
        headers=other_auth_headers,
        json={"token": token},
    )
    assert reuse.status_code == 404


def test_join_already_member_conflict(
    client: TestClient,
    user: User,
    other_user: User,
    account: Account,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
) -> None:
    token = client.post(
        f"/v1/accounts/{account.uid}/invites", headers=auth_headers
    ).json()["token"]
    assert (
        client.post(
            "/v1/accounts/join",
            headers=other_auth_headers,
            json={"token": token},
        ).status_code
        == 200
    )

    second = client.post(f"/v1/accounts/{account.uid}/invites", headers=auth_headers)
    assert second.status_code == 200
    assert (
        client.post(
            "/v1/accounts/join",
            headers=other_auth_headers,
            json={"token": second.json()["token"]},
        ).status_code
        == 409
    )


def test_member_cannot_invite_or_delete(
    client: TestClient,
    db: Session,
    user: User,
    other_user: User,
    account: Account,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
) -> None:
    token = client.post(
        f"/v1/accounts/{account.uid}/invites", headers=auth_headers
    ).json()["token"]
    assert (
        client.post(
            "/v1/accounts/join",
            headers=other_auth_headers,
            json={"token": token},
        ).status_code
        == 200
    )

    assert (
        client.post(
            f"/v1/accounts/{account.uid}/invites", headers=other_auth_headers
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/v1/accounts/{account.uid}",
            headers=other_auth_headers,
            json={"name": "hack"},
        ).status_code
        == 403
    )
    assert (
        client.delete(f"/v1/accounts/{account.uid}", headers=other_auth_headers).status_code
        == 403
    )


def test_member_can_create_transaction_on_shared_account(
    client: TestClient,
    account: Account,
    system_categories: dict[str, Category],
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
) -> None:
    token = client.post(
        f"/v1/accounts/{account.uid}/invites", headers=auth_headers
    ).json()["token"]
    assert (
        client.post(
            "/v1/accounts/join",
            headers=other_auth_headers,
            json={"token": token},
        ).status_code
        == 200
    )

    created = client.post(
        "/v1/transactions",
        headers=other_auth_headers,
        json={
            "account_id": account.uid,
            "type": "expense",
            "amount": 50_00,
            "currency": "RUB",
            "occurred_at": "2026-06-20T10:00:00",
            "category_id": system_categories["other"].uid,
            "comment": "общий расход",
        },
    )
    assert created.status_code == 200

    listed = client.get(
        "/v1/transactions",
        headers=auth_headers,
        params={"from": "2026-06-01", "to": "2026-06-30", "account_id": account.uid},
    )
    assert listed.status_code == 200
    assert any(t["amount"] == 50_00 for t in listed.json()["transactions"])


def test_list_accounts_includes_members(
    client: TestClient,
    user: User,
    account: Account,
    auth_headers: dict[str, str],
) -> None:
    listed = client.get("/v1/accounts", headers=auth_headers)
    assert listed.status_code == 200
    acc = next(a for a in listed.json()["accounts"] if a["id"] == account.uid)
    assert len(acc["members"]) == 1
    assert acc["members"][0]["id"] == user.uid
    assert acc["members"][0]["role"] == AccountMemberRole.OWNER.value
    assert acc["members"][0]["login"] == user.login


def test_unknown_invite_token(
    client: TestClient, other_auth_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/v1/accounts/join",
        headers=other_auth_headers,
        json={"token": "00000000-0000-0000-0000-000000000000"},
    )
    assert resp.status_code == 404
