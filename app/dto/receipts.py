"""DTO для чеков."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.dto.transactions import MerchantBriefDTO, TransactionDetailDTO, TransactionItemBriefDTO


class QrReceiptRequestDTO(BaseModel):
    account_id: str = Field(description="UUID счёта для списания")
    qr: str = Field(min_length=10, description="Строка QR-кода с чека (ФН, ФД, ФП, дата, сумма)")


class QrReceiptResponseDTO(BaseModel):
    transaction: TransactionDetailDTO = Field(description="Созданная транзакция с позициями чека")


# --- Receipt Provider DTOs ---


class ReceiptProviderInputDTO(BaseModel):
    qr: str


class ReceiptMerchantDTO(BaseModel):
    name: str
    inn: str | None = None
    address: str | None = None


class ReceiptMetaDTO(BaseModel):
    fiscal_drive_number: str | None = None
    fiscal_document_number: str | None = None
    fiscal_sign: str | None = None
    operation_type: int | None = None
    receipt_datetime: datetime | None = None
    total_sum: int


class ReceiptItemDTO(BaseModel):
    raw_name: str
    price: int
    quantity: int
    amount: int
    gtin: str | None = None


class ReceiptProviderOutputDTO(BaseModel):
    raw: dict
    merchant: ReceiptMerchantDTO
    receipt: ReceiptMetaDTO
    items: list[ReceiptItemDTO]


# --- Product Normalizer DTOs ---


class NormalizerInputItemDTO(BaseModel):
    raw_name: str
    price: int
    quantity: int


class ProductNormalizerInputDTO(BaseModel):
    merchant: str | None
    items: list[NormalizerInputItemDTO]


class NormalizedItemDTO(BaseModel):
    raw_name: str
    normalized_name: str
    product_name: str
    brand: str | None = None
    category: str
    subcategory: str | None = None
    confidence: float


class ProductNormalizerOutputDTO(BaseModel):
    items: list[NormalizedItemDTO]
