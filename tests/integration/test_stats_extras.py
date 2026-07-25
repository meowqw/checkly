"""Stats: account filter, empty period, recent limit."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.uuid_utils import new_uid
from app.database.models import Account, Category, User, UserAccount
from app.dto.transactions import TransactionFilterDTO
from app.services.stats_service import StatsService
from tests.conftest import make_manual_tx


def test_stats_empty_period(db: Session, user: User, account: Account) -> None:
    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2020, 1, 1),
            to_date=datetime(2020, 1, 31),
            timezone="Europe/Moscow",
        )
    )
    assert stats.expense == 0
    assert stats.income == 0
    assert stats.categories == []
    assert stats.recent_expenses == []


def test_stats_account_filter(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    other = Account(uid=new_uid(), name="Другой", balance=0)
    db.add(other)
    db.flush()
    db.add(UserAccount(user_id=user.id, account_id=other.id))
    db.commit()
    db.refresh(other)

    make_manual_tx(
        db,
        user=user,
        account=account,
        amount=100_00,
        category=system_categories["other"],
        occurred_at=datetime(2026, 6, 5, 12, 0, 0),
    )
    make_manual_tx(
        db,
        user=user,
        account=other,
        amount=999_00,
        category=system_categories["other"],
        occurred_at=datetime(2026, 6, 5, 13, 0, 0),
        comment="other-acc",
    )

    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            account_uid=account.uid,
            timezone="Europe/Moscow",
        )
    )
    assert stats.expense == 100_00


def test_recent_expenses_capped_at_8(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    for i in range(12):
        make_manual_tx(
            db,
            user=user,
            account=account,
            amount=10_00 + i,
            category=system_categories["other"],
            occurred_at=datetime(2026, 6, 1, 12, 0, 0 + i),
            comment=f"e-{i}",
        )
    stats = StatsService(db).get_stats(
        TransactionFilterDTO(
            user_id=user.id,
            from_date=datetime(2026, 6, 1),
            to_date=datetime(2026, 6, 30),
            timezone="Europe/Moscow",
        )
    )
    assert len(stats.recent_expenses) == 8
