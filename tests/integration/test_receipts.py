"""QR-чек: создание через моки provider/normalizer, баланс, fallback LLM."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import TransactionSource
from app.core.exceptions import ExternalServiceError, NotFoundError
from app.core.uuid_utils import new_uid
from app.database.models import Account, Category, Product, User
from app.dto.receipts import (
    NormalizedItemDTO,
    ProductNormalizerOutputDTO,
    ReceiptItemDTO,
)
from app.dto.transactions import CreateTransactionFromReceiptDTO
from app.services.transaction_service import TransactionService
from tests.helpers import FakeProductNormalizer, FakeReceiptProvider, default_receipt_output
import pytest


def test_create_from_receipt_decreases_balance_and_creates_items(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    before = account.balance
    provider = FakeReceiptProvider(
        default_receipt_output(total_sum=500_00)
    )
    normalizer = FakeProductNormalizer()
    service = TransactionService(db, receipt_provider=provider, product_normalizer=normalizer)

    result = service.create_transaction_from_receipt(
        CreateTransactionFromReceiptDTO(
            user_id=user.id,
            account_uid=account.uid,
            qr="t=20260610T1530&s=500.00&fn=1&i=1&fp=1&n=1",
            timezone="Europe/Moscow",
        )
    )
    db.refresh(account)
    assert account.balance == before - 500_00
    assert result.transaction.source == TransactionSource.QR_RECEIPT.value
    assert result.transaction.amount == 500_00
    assert result.transaction.items is not None
    assert len(result.transaction.items) == 2
    assert provider.calls
    assert normalizer.calls == 1


def test_create_from_receipt_reuses_known_product_by_gtin(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    product = Product(
        uid=new_uid(),
        name="Молоко",
        normalized_name="Молоко",
        gtin="4600000000001",
        category_id=system_categories["dairy"].id,
    )
    db.add(product)
    db.commit()

    provider = FakeReceiptProvider(
        default_receipt_output(
            total_sum=200_00,
            items=[
                ReceiptItemDTO(
                    raw_name="МОЛОКО ДРУГОЕ ИМЯ",
                    price=200_00,
                    quantity=1,
                    amount=200_00,
                    gtin="4600000000001",
                )
            ],
        )
    )
    normalizer = FakeProductNormalizer()
    service = TransactionService(db, receipt_provider=provider, product_normalizer=normalizer)
    result = service.create_transaction_from_receipt(
        CreateTransactionFromReceiptDTO(
            user_id=user.id,
            account_uid=account.uid,
            qr="t=20260610T1530&s=200.00&fn=1&i=1&fp=1&n=1",
            timezone="Europe/Moscow",
        )
    )
    assert normalizer.calls == 0  # known by gtin — LLM не нужен
    assert result.transaction.items is not None
    assert result.transaction.items[0].category_id == system_categories["dairy"].uid


def test_create_from_receipt_llm_fallback_to_prochee(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    provider = FakeReceiptProvider(
        default_receipt_output(
            total_sum=100_00,
            items=[
                ReceiptItemDTO(raw_name="НЕИЗВЕСТНОЕ", price=100_00, quantity=1, amount=100_00)
            ],
        )
    )
    service = TransactionService(
        db,
        receipt_provider=provider,
        product_normalizer=FakeProductNormalizer(fail=True),
    )
    result = service.create_transaction_from_receipt(
        CreateTransactionFromReceiptDTO(
            user_id=user.id,
            account_uid=account.uid,
            qr="t=20260610T1530&s=100.00&fn=1&i=1&fp=1&n=1",
            timezone="Europe/Moscow",
        )
    )
    assert result.transaction.items is not None
    assert result.transaction.items[0].category_id == system_categories["other"].uid


def test_create_from_receipt_unknown_account(
    db: Session, user: User
) -> None:
    service = TransactionService(
        db,
        receipt_provider=FakeReceiptProvider(),
        product_normalizer=FakeProductNormalizer(),
    )
    with pytest.raises(NotFoundError):
        service.create_transaction_from_receipt(
            CreateTransactionFromReceiptDTO(
                user_id=user.id,
                account_uid="00000000-0000-0000-0000-000000000001",
                qr="t=20260610T1530&s=100.00&fn=1&i=1&fp=1&n=1",
                timezone="Europe/Moscow",
            )
        )


def test_create_from_receipt_provider_error_propagates(
    db: Session, user: User, account: Account
) -> None:
    class Boom(FakeReceiptProvider):
        def get_receipt_by_qr(self, dto):  # noqa: ANN001
            raise ExternalServiceError("proverkacheka down")

    service = TransactionService(
        db, receipt_provider=Boom(), product_normalizer=FakeProductNormalizer()
    )
    with pytest.raises(ExternalServiceError):
        service.create_transaction_from_receipt(
            CreateTransactionFromReceiptDTO(
                user_id=user.id,
                account_uid=account.uid,
                qr="t=20260610T1530&s=100.00&fn=1&i=1&fp=1&n=1",
                timezone="Europe/Moscow",
            )
        )


def test_second_scan_matches_alias(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    """После первого чека alias известен — второй не ходит в LLM."""
    provider = FakeReceiptProvider(
        default_receipt_output(
            total_sum=100_00,
            items=[
                ReceiptItemDTO(raw_name="УНИКАЛЬНЫЙ ТОВАР", price=100_00, quantity=1, amount=100_00)
            ],
        )
    )
    normalizer = FakeProductNormalizer(
        ProductNormalizerOutputDTO(
            items=[
                NormalizedItemDTO(
                    raw_name="УНИКАЛЬНЫЙ ТОВАР",
                    normalized_name="Уникальный товар",
                    product_name="Уникальный товар",
                    category="Продукты",
                    subcategory="Снэки",
                    confidence=0.95,
                )
            ]
        )
    )
    service = TransactionService(db, receipt_provider=provider, product_normalizer=normalizer)
    dto = CreateTransactionFromReceiptDTO(
        user_id=user.id,
        account_uid=account.uid,
        qr="t=20260610T1530&s=100.00&fn=1&i=1&fp=1&n=1",
        timezone="Europe/Moscow",
    )
    service.create_transaction_from_receipt(dto)
    assert normalizer.calls == 1

    service.create_transaction_from_receipt(dto)
    assert normalizer.calls == 1  # второй раз — через alias
