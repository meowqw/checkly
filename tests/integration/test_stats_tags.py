"""Разбивка статистики по тегам."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import Account, User
from app.dto.transactions import TransactionFilterDTO
from app.services.stats_service import StatsService
from tests.conftest import make_manual_tx, make_qr_tx


def test_stats_tags_breakdown_by_items(
    db: Session, user: User, account: Account, system_categories: dict
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=500_00,
        category=system_categories["products"],
        tags=[system_categories["dairy"]],
        occurred_at=datetime(2026, 6, 2, 10, 0, 0),
        comment="Молоко",
    )
    make_qr_tx(
        db,
        user=user,
        account=account,
        occurred_at=datetime(2026, 6, 3, 12, 0, 0),
        items=[
            ("Молоко", 200_00, system_categories["products"], [system_categories["dairy"]]),
            ("Чипсы", 300_00, system_categories["products"], [system_categories["snacks"]]),
            ("Хлеб", 100_00, system_categories["products"], None),
        ],
    )
    # orphan без позиций → «Без тега»
    from app.core.enums import Currency, TransactionSource, TransactionType
    from app.core.uuid_utils import new_uid
    from app.database.models import Transaction

    orphan = Transaction(
        uid=new_uid(),
        user_id=user.id,
        account_id=account.id,
        type=TransactionType.EXPENSE.value,
        amount=50_00,
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

    by_name = {t.name: t for t in stats.tags}
    assert by_name["Молочные"].amount == 700_00  # 500 + 200
    assert by_name["Снэки"].amount == 300_00
    assert by_name["Без тега"].amount == 150_00  # 100 bread + 50 orphan
    assert by_name["Молочные"].tag_id == system_categories["dairy"].uid
    assert by_name["Без тега"].tag_id is None
    assert stats.tags[0].amount >= stats.tags[-1].amount
    assert sum(t.percent for t in stats.tags) in (99, 100, 101)


def test_stats_tags_multi_tag_counts_full_amount(
    db: Session, user: User, account: Account, system_categories: dict
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=400_00,
        category=system_categories["products"],
        tags=[system_categories["dairy"], system_categories["snacks"]],
        occurred_at=datetime(2026, 6, 5, 10, 0, 0),
    )
    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            timezone="Europe/Moscow",
        )
    )
    by_name = {t.name: t for t in stats.tags}
    assert by_name["Молочные"].amount == 400_00
    assert by_name["Снэки"].amount == 400_00


def test_stats_tags_respect_tag_filter(
    db: Session, user: User, account: Account, system_categories: dict
) -> None:
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=500_00,
        category=system_categories["products"],
        tags=[system_categories["dairy"]],
        occurred_at=datetime(2026, 6, 2, 10, 0, 0),
    )
    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=300_00,
        category=system_categories["products"],
        tags=[system_categories["snacks"]],
        occurred_at=datetime(2026, 6, 3, 10, 0, 0),
    )
    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            tag_uid=system_categories["dairy"].uid,
            timezone="Europe/Moscow",
        )
    )
    assert stats.expense == 500_00
    assert len(stats.tags) == 1
    assert stats.tags[0].name == "Молочные"
    assert stats.tags[0].amount == 500_00
