"""Фильтр stats по category_id (ветка / подкатегория)."""
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models import Account, Category, User
from app.dto.transactions import TransactionFilterDTO
from app.services.stats_service import StatsService
from tests.conftest import make_manual_tx, make_qr_tx


def _seed_mixed(
    db: Session, user: User, account: Account, cats: dict[str, Category]
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=10_000_00,
        tx_type="income",
        category=cats["salary"],
        occurred_at=datetime(2026, 6, 1, 10, 0, 0),
        comment="Зарплата",
    )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=500_00,
        category=cats["dairy"],
        occurred_at=datetime(2026, 6, 2, 10, 0, 0),
        comment="Молоко",
    )
    make_qr_tx(
        db,
        user=user,
        account=account,
        occurred_at=datetime(2026, 6, 3, 12, 0, 0),
        items=[
            ("Молоко", 200_00, cats["dairy"]),
            ("Чипсы", 300_00, cats["snacks"]),
        ],
    )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=100_00,
        category=cats["other"],
        occurred_at=datetime(2026, 6, 4, 9, 0, 0),
        comment="Прочее",
    )


def test_stats_filter_by_parent_includes_children(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    _seed_mixed(db, user, account, system_categories)
    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            category_uid=system_categories["products"].uid,
            timezone="Europe/Moscow",
        )
    )
    # Молочные 700 + Снэки 300; income по expense-ветке = 0
    assert stats.expense == 1_000_00
    assert stats.income == 0
    by_name = {c.name: c.amount for c in stats.categories}
    assert by_name == {
        "Продукты › Молочные": 700_00,
        "Продукты › Снэки": 300_00,
    }
    assert "Прочее" not in by_name
    assert len(stats.recent_expenses) >= 1
    assert all(t.type == "expense" for t in stats.recent_expenses)


def test_stats_filter_by_subcategory(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    _seed_mixed(db, user, account, system_categories)
    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            category_uid=system_categories["dairy"].uid,
            timezone="Europe/Moscow",
        )
    )
    assert stats.expense == 700_00
    assert stats.income == 0
    assert len(stats.categories) == 1
    assert stats.categories[0].name == "Продукты › Молочные"
    assert stats.categories[0].percent == 100


def test_stats_filter_by_income_category(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    _seed_mixed(db, user, account, system_categories)
    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            category_uid=system_categories["salary"].uid,
            timezone="Europe/Moscow",
        )
    )
    assert stats.income == 10_000_00
    assert stats.expense == 0
    assert stats.categories == []
    assert stats.recent_expenses == []


def test_stats_unknown_category(
    db: Session, user: User, account: Account
) -> None:
    with pytest.raises(NotFoundError):
        StatsService(db).get_stats(
            TransactionFilterDTO(
                user_id=user.id,
                category_uid="00000000-0000-0000-0000-000000000099",
                timezone="Europe/Moscow",
            )
        )
