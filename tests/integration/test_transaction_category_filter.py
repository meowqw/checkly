"""Фильтр списка транзакций по category_id."""
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models import Account, Category, User
from app.dto.transactions import TransactionFilterDTO
from app.services.transaction_service import TransactionService
from tests.conftest import make_manual_tx, make_qr_tx


def test_list_filter_by_parent_category(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=500_00,
        category=system_categories["dairy"],
        occurred_at=datetime(2026, 6, 2, 10, 0, 0),
        comment="dairy",
    )
    make_qr_tx(
        db,
        user=user,
        account=account,
        occurred_at=datetime(2026, 6, 3, 12, 0, 0),
        items=[
            ("Молоко", 200_00, system_categories["dairy"]),
            ("Чипсы", 300_00, system_categories["snacks"]),
        ],
    )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=100_00,
        category=system_categories["other"],
        occurred_at=datetime(2026, 6, 4, 9, 0, 0),
        comment="other",
    )

    result = TransactionService(db).list_transactions(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            category_uid=system_categories["products"].uid,
            timezone="Europe/Moscow",
        )
    )
    comments = {t.comment for t in result.transactions}
    # manual dairy + qr (есть позиции продуктов); other не входит
    assert len(result.transactions) == 2
    assert "other" not in comments


def test_list_filter_by_subcategory(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=500_00,
        category=system_categories["dairy"],
        comment="dairy",
    )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=100_00,
        category=system_categories["snacks"],
        occurred_at=datetime(2026, 6, 16, 12, 0, 0),
        comment="snacks",
    )
    result = TransactionService(db).list_transactions(
        TransactionFilterDTO(
            user_id=user.id,
            category_uid=system_categories["dairy"].uid,
            timezone="Europe/Moscow",
        )
    )
    assert len(result.transactions) == 1
    assert result.transactions[0].comment == "dairy"


def test_list_category_filter_with_pagination(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    for i in range(3):
        make_manual_tx(
            db,
            user=user,
            account=account,
            amount=10_00 + i,
            category=system_categories["dairy"],
            occurred_at=datetime(2026, 6, 1 + i, 12, 0, 0),
            comment=f"d-{i}",
        )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=99_00,
        category=system_categories["other"],
        occurred_at=datetime(2026, 6, 10, 12, 0, 0),
        comment="skip",
    )
    page = TransactionService(db).list_transactions(
        TransactionFilterDTO(
            user_id=user.id,
            category_uid=system_categories["dairy"].uid,
            timezone="Europe/Moscow",
            limit=2,
            offset=0,
        )
    )
    assert page.total == 3
    assert len(page.transactions) == 2
    assert page.has_more is True


def test_list_unknown_category(
    db: Session, user: User, account: Account
) -> None:
    with pytest.raises(NotFoundError):
        TransactionService(db).list_transactions(
            TransactionFilterDTO(
                user_id=user.id,
                category_uid="00000000-0000-0000-0000-000000000099",
                timezone="Europe/Moscow",
            )
        )
