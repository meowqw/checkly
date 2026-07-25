"""Пагинация: clamp limit, offset beyond end, date inclusive bounds."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import Account, Category, User
from app.dto.transactions import TransactionFilterDTO
from app.services.transaction_service import TRANSACTIONS_MAX_LIMIT, TransactionService
from tests.conftest import make_manual_tx


def test_limit_clamped_to_max(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    for i in range(3):
        make_manual_tx(
            db,
            user=user,
            account=account,
            amount=10_00,
            category=system_categories["other"],
            occurred_at=datetime(2026, 6, 1 + i, 12, 0, 0),
            comment=f"c-{i}",
        )
    page = TransactionService(db).list_transactions(
        TransactionFilterDTO(
            user_id=user.id,
            timezone="Europe/Moscow",
            limit=TRANSACTIONS_MAX_LIMIT + 50,
            offset=0,
        )
    )
    assert page.limit == TRANSACTIONS_MAX_LIMIT
    assert page.total == 3
    assert len(page.transactions) == 3
    assert page.has_more is False


def test_offset_past_end(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    make_manual_tx(
        db, user=user, account=account, amount=10_00, category=system_categories["other"]
    )
    page = TransactionService(db).list_transactions(
        TransactionFilterDTO(
            user_id=user.id,
            timezone="Europe/Moscow",
            limit=10,
            offset=100,
        )
    )
    assert page.total == 1
    assert page.transactions == []
    assert page.has_more is False


def test_date_range_includes_boundary_day(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=10_00,
        category=system_categories["other"],
        occurred_at=datetime(2026, 6, 15, 23, 50, 0),
    )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=20_00,
        category=system_categories["other"],
        occurred_at=datetime(2026, 6, 16, 0, 10, 0),
        comment="next-day",
    )
    result = TransactionService(db).list_transactions(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 15),
            to_date=datetime(2026, 6, 15),
            timezone="Europe/Moscow",
        )
    )
    assert len(result.transactions) == 1
    assert result.transactions[0].amount == 10_00
