"""DTO для транзакций."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import Currency, TransactionSource, TransactionType


class AccountBriefDTO(BaseModel):
    id: str
    name: str


class MerchantBriefDTO(BaseModel):
    id: str | None = None
    name: str


class TransactionItemBriefDTO(BaseModel):
    id: str | None = None
    raw_name: str
    amount: int
    category_id: str | None = None
    category: dict | None = None


class TransactionListItemDTO(BaseModel):
    id: str
    type: str
    amount: int
    currency: str
    occurred_at: datetime
    source: str
    comment: str | None = None
    title: str
    account: AccountBriefDTO | None = None
    merchant: MerchantBriefDTO | None = None
    category: str | None = None
    items_count: int = 0
    items: list[TransactionItemBriefDTO] | None = None


class TransactionsListResponseDTO(BaseModel):
    transactions: list[TransactionListItemDTO]


class CreateManualTransactionRequestDTO(BaseModel):
    account_id: str
    type: TransactionType
    amount: int = Field(gt=0)
    currency: Currency = Currency.RUB
    occurred_at: datetime
    category_id: str | None = None
    comment: str | None = None


class UpdateTransactionRequestDTO(BaseModel):
    amount: int | None = Field(default=None, gt=0)
    category_id: str | None = None
    comment: str | None = None


class TransactionDetailDTO(BaseModel):
    id: str
    amount: int
    source: str
    type: str | None = None
    currency: str | None = None
    occurred_at: datetime | None = None
    comment: str | None = None
    merchant: MerchantBriefDTO | None = None
    items: list[TransactionItemBriefDTO] | None = None


class TransactionResponseDTO(BaseModel):
    transaction: TransactionDetailDTO


class TransactionFilterDTO(BaseModel):
    user_id: int
    from_date: datetime | None = None
    to_date: datetime | None = None
    type: TransactionType | None = None
    account_uid: str | None = None
    timezone: str = "Europe/Moscow"


class CreateManualTransactionDTO(BaseModel):
    user_id: int
    account_uid: str
    type: TransactionType
    amount: int
    currency: Currency
    occurred_at: datetime
    category_uid: str | None = None
    comment: str | None = None
    timezone: str = "Europe/Moscow"


class UpdateTransactionDTO(BaseModel):
    user_id: int
    transaction_uid: str
    amount: int | None = None
    category_uid: str | None = None
    comment: str | None = None


class UpdateTransactionItemRequestDTO(BaseModel):
    category_id: str


class UpdateTransactionItemDTO(BaseModel):
    user_id: int
    transaction_uid: str
    item_uid: str
    category_uid: str


class CreateTransactionFromReceiptDTO(BaseModel):
    user_id: int
    account_uid: str
    qr: str
    timezone: str = "Europe/Moscow"
