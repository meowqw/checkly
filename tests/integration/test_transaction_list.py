"""Список транзакций: фильтры и пагинация."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import TransactionType
from app.core.exceptions import NotFoundError
from app.database.models import Account, Category, User
from app.dto.transactions import TransactionFilterDTO
from app.services.transaction_service import TransactionService
from tests.conftest import make_manual_tx
import pytest


def test_list_without_limit_has_no_pagination_meta(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    make_manual_tx(
        db, user=user, account=account, amount=100_00, category=system_categories["other"]
    )
    result = TransactionService(db).list_transactions(
        TransactionFilterDTO(user_id=user.id, timezone="Europe/Moscow")
    )
    assert len(result.transactions) == 1
    assert result.total is None
    assert result.has_more is None


def test_list_pagination_meta(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    for i in range(5):
        make_manual_tx(
            db,
            user=user,
            account=account,
            amount=100_00 + i,
            category=system_categories["other"],
            occurred_at=datetime(2026, 6, 1 + i, 12, 0, 0),
            comment=f"tx-{i}",
        )
    page = TransactionService(db).list_transactions(
        TransactionFilterDTO(
            user_id=user.id,
            timezone="Europe/Moscow",
            limit=2,
            offset=0,
        )
    )
    assert page.total == 5
    assert page.limit == 2
    assert page.offset == 0
    assert page.has_more is True
    assert len(page.transactions) == 2
    # newest first
    assert page.transactions[0].occurred_at > page.transactions[1].occurred_at

    last = TransactionService(db).list_transactions(
        TransactionFilterDTO(
            user_id=user.id,
            timezone="Europe/Moscow",
            limit=2,
            offset=4,
        )
    )
    assert last.has_more is False
    assert len(last.transactions) == 1


def test_list_filter_by_type(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=100_00,
        category=system_categories["other"],
    )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=500_00,
        tx_type="income",
        category=system_categories["salary"],
        comment="income",
    )
    expenses = TransactionService(db).list_transactions(
        TransactionFilterDTO(
            user_id=user.id,
            type=TransactionType.EXPENSE,
            timezone="Europe/Moscow",
        )
    )
    assert len(expenses.transactions) == 1
    assert expenses.transactions[0].type == "expense"


def test_list_unknown_account_raises(
    db: Session, user: User, account: Account
) -> None:
    with pytest.raises(NotFoundError):
        TransactionService(db).list_transactions(
            TransactionFilterDTO(
                user_id=user.id,
                account_uid="00000000-0000-0000-0000-000000000000",
                timezone="Europe/Moscow",
            )
        )
