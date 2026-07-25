"""Агрегация статистики: суммы, категории по позициям, recent."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import Account, Category, User
from app.dto.transactions import TransactionFilterDTO
from app.services.stats_service import StatsService
from tests.conftest import make_manual_tx, make_qr_tx


def test_stats_sums_and_categories_by_items(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=10_000_00,
        tx_type="income",
        category=system_categories["salary"],
        occurred_at=datetime(2026, 6, 1, 10, 0, 0),
        comment="Зарплата",
    )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=500_00,
        category=system_categories["dairy"],
        occurred_at=datetime(2026, 6, 2, 10, 0, 0),
        comment="Молоко",
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
    # расход без позиций → «Прочее»
    from app.core.enums import Currency, TransactionSource, TransactionType
    from app.core.uuid_utils import new_uid
    from app.database.models import Transaction

    orphan = Transaction(
        uid=new_uid(),
        user_id=user.id,
        account_id=account.id,
        type=TransactionType.EXPENSE.value,
        amount=100_00,
        currency=Currency.RUB.value,
        occurred_at=datetime(2026, 6, 4, 9, 0, 0),
        source=TransactionSource.MANUAL.value,
        comment="без позиций",
    )
    db.add(orphan)
    db.commit()

    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            timezone="Europe/Moscow",
        )
    )

    assert stats.income == 10_000_00
    assert stats.expense == 500_00 + 500_00 + 100_00  # manual + qr total + orphan
    by_name = {c.name: c for c in stats.categories}
    assert by_name["Продукты › Молочные"].amount == 700_00  # 500 + 200
    assert by_name["Продукты › Снэки"].amount == 300_00
    assert by_name["Прочее"].amount == 100_00
    assert sum(c.percent for c in stats.categories) in (99, 100, 101)  # round
    assert len(stats.recent_expenses) <= 8
    assert all(t.type == "expense" for t in stats.recent_expenses)


def test_stats_respects_date_filter(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=100_00,
        category=system_categories["other"],
        occurred_at=datetime(2026, 5, 1, 12, 0, 0),
    )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=200_00,
        category=system_categories["other"],
        occurred_at=datetime(2026, 6, 15, 12, 0, 0),
    )
    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            timezone="Europe/Moscow",
        )
    )
    assert stats.expense == 200_00
