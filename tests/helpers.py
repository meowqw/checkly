"""Фейковые внешние зависимости для тестов QR/нормализации."""
from __future__ import annotations

from datetime import datetime

from app.dto.receipts import (
    NormalizedItemDTO,
    ProductNormalizerInputDTO,
    ProductNormalizerOutputDTO,
    ReceiptItemDTO,
    ReceiptMerchantDTO,
    ReceiptMetaDTO,
    ReceiptProviderInputDTO,
    ReceiptProviderOutputDTO,
)
from app.interfaces.product_normalizer import ProductNormalizerInterface
from app.interfaces.receipt_provider import ReceiptProviderInterface


class FakeReceiptProvider(ReceiptProviderInterface):
    def __init__(self, output: ReceiptProviderOutputDTO | None = None):
        self.output = output or default_receipt_output()
        self.calls: list[str] = []

    def get_receipt_by_qr(self, dto: ReceiptProviderInputDTO) -> ReceiptProviderOutputDTO:
        self.calls.append(dto.qr)
        return self.output


class FakeProductNormalizer(ProductNormalizerInterface):
    def __init__(self, output: ProductNormalizerOutputDTO | None = None, *, fail: bool = False):
        self.fail = fail
        self.output = output
        self.calls = 0

    def normalize_items(self, dto: ProductNormalizerInputDTO) -> ProductNormalizerOutputDTO:
        self.calls += 1
        if self.fail:
            from app.core.exceptions import ExternalServiceError

            raise ExternalServiceError("LLM недоступен")
        if self.output:
            return self.output
        return ProductNormalizerOutputDTO(
            items=[
                NormalizedItemDTO(
                    raw_name=item.raw_name,
                    normalized_name=item.raw_name.title(),
                    product_name=item.raw_name.title(),
                    brand=None,
                    category="Продукты",
                    subcategory="Молочные",
                    confidence=0.9,
                )
                for item in dto.items
            ]
        )


def default_receipt_output(
    *,
    total_sum: int = 500_00,
    items: list[ReceiptItemDTO] | None = None,
) -> ReceiptProviderOutputDTO:
    if items is None:
        items = [
            ReceiptItemDTO(
                raw_name="МОЛОКО 1Л",
                price=200_00,
                quantity=1,
                amount=200_00,
                gtin=None,
            ),
            ReceiptItemDTO(
                raw_name="ЧИПСЫ LAYS",
                price=300_00,
                quantity=1,
                amount=300_00,
                gtin=None,
            ),
        ]
    return ReceiptProviderOutputDTO(
        raw={"seed": True},
        merchant=ReceiptMerchantDTO(
            name="ООО ТестМаг",
            inn="7700000000",
            address="Москва",
        ),
        receipt=ReceiptMetaDTO(
            fiscal_drive_number="9999000001",
            fiscal_document_number="12345",
            fiscal_sign="987654321",
            operation_type=1,
            receipt_datetime=datetime(2026, 6, 10, 15, 30, 0),
            total_sum=total_sum,
        ),
        items=items,
    )
