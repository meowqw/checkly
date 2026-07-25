"""Баланс счёта при create / update / delete ручных транзакций."""
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.core.enums import Currency, TransactionType
from app.core.exceptions import ForbiddenError
from app.database.models import Account, Category, User
from app.dto.transactions import CreateManualTransactionDTO, UpdateTransactionDTO
from app.services.transaction_service import TransactionService
from tests.conftest import make_qr_tx


def _balance(db: Session, account: Account) -> int:
    db.refresh(account)
    return account.balance


def test_create_expense_decreases_balance(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    before = account.balance
    TransactionService(db).create_manual_transaction(
        CreateManualTransactionDTO(
            user_id=user.id,
            account_uid=account.uid,
            type=TransactionType.EXPENSE,
            amount=1_500_00,
            currency=Currency.RUB,
            occurred_at=datetime(2026, 6, 1, 12, 0, 0),
            category_uid=system_categories["dairy"].uid,
            comment="Молоко",
            timezone="Europe/Moscow",
        )
    )
    assert _balance(db, account) == before - 1_500_00


def test_create_income_increases_balance(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    before = account.balance
    TransactionService(db).create_manual_transaction(
        CreateManualTransactionDTO(
            user_id=user.id,
            account_uid=account.uid,
            type=TransactionType.INCOME,
            amount=50_000_00,
            currency=Currency.RUB,
            occurred_at=datetime(2026, 6, 1, 12, 0, 0),
            category_uid=system_categories["salary"].uid,
            comment="Зарплата",
            timezone="Europe/Moscow",
        )
    )
    assert _balance(db, account) == before + 50_000_00


def test_update_expense_amount_applies_delta(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    service = TransactionService(db)
    created = service.create_manual_transaction(
        CreateManualTransactionDTO(
            user_id=user.id,
            account_uid=account.uid,
            type=TransactionType.EXPENSE,
            amount=1_000_00,
            currency=Currency.RUB,
            occurred_at=datetime(2026, 6, 1, 12, 0, 0),
            category_uid=system_categories["dairy"].uid,
            comment="x",
            timezone="Europe/Moscow",
        )
    )
    after_create = _balance(db, account)
    service.update_transaction(
        UpdateTransactionDTO(
            user_id=user.id,
            transaction_uid=created.transaction.id,
            amount=1_500_00,
        )
    )
    assert _balance(db, account) == after_create - 500_00

    service.update_transaction(
        UpdateTransactionDTO(
            user_id=user.id,
            transaction_uid=created.transaction.id,
            amount=800_00,
        )
    )
    assert _balance(db, account) == after_create - 500_00 + 700_00


def test_delete_expense_restores_balance(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    before = account.balance
    service = TransactionService(db)
    created = service.create_manual_transaction(
        CreateManualTransactionDTO(
            user_id=user.id,
            account_uid=account.uid,
            type=TransactionType.EXPENSE,
            amount=2_000_00,
            currency=Currency.RUB,
            occurred_at=datetime(2026, 6, 1, 12, 0, 0),
            category_uid=system_categories["other"].uid,
            comment="x",
            timezone="Europe/Moscow",
        )
    )
    assert _balance(db, account) == before - 2_000_00
    service.delete_transaction(user.id, created.transaction.id)
    assert _balance(db, account) == before


def test_delete_income_restores_balance(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    before = account.balance
    service = TransactionService(db)
    created = service.create_manual_transaction(
        CreateManualTransactionDTO(
            user_id=user.id,
            account_uid=account.uid,
            type=TransactionType.INCOME,
            amount=10_000_00,
            currency=Currency.RUB,
            occurred_at=datetime(2026, 6, 1, 12, 0, 0),
            category_uid=system_categories["salary"].uid,
            comment="x",
            timezone="Europe/Moscow",
        )
    )
    service.delete_transaction(user.id, created.transaction.id)
    assert _balance(db, account) == before


def test_cannot_update_qr_transaction(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    qr = make_qr_tx(
        db,
        user=user,
        account=account,
        items=[("Молоко", 100_00, system_categories["dairy"])],
    )
    with pytest.raises(ForbiddenError):
        TransactionService(db).update_transaction(
            UpdateTransactionDTO(
                user_id=user.id,
                transaction_uid=qr.uid,
                amount=50_00,
            )
        )
