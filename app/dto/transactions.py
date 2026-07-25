"""DTO для транзакций."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import Currency, TransactionSource, TransactionType


class AccountBriefDTO(BaseModel):
    id: str = Field(description="UUID счёта")
    name: str = Field(description="Название счёта")


class MerchantBriefDTO(BaseModel):
    id: str | None = Field(default=None, description="UUID магазина")
    name: str = Field(description="Название магазина")


class CategoryBriefDTO(BaseModel):
    name: str = Field(description="Отображаемое имя категории")


class TransactionItemBriefDTO(BaseModel):
    id: str | None = Field(default=None, description="UUID позиции чека")
    raw_name: str = Field(description="Название товара из чека")
    amount: int = Field(description="Сумма позиции в копейках")
    category_id: str | None = Field(default=None, description="UUID категории")
    category: CategoryBriefDTO | None = Field(default=None, description="Краткая информация о категории")


class TransactionListItemDTO(BaseModel):
    id: str = Field(description="UUID транзакции")
    type: str = Field(description="Тип: expense или income")
    amount: int = Field(description="Сумма в копейках")
    currency: str = Field(description="Валюта (RUB)")
    occurred_at: datetime = Field(description="Дата и время операции")
    source: str = Field(description="Источник: manual, qr_receipt, ocr, import")
    comment: str | None = Field(default=None, description="Комментарий")
    title: str = Field(description="Заголовок для списка (категория, магазин или комментарий)")
    account: AccountBriefDTO | None = Field(default=None, description="Счёт")
    merchant: MerchantBriefDTO | None = Field(default=None, description="Магазин (для чеков)")
    category: str | None = Field(
        default=None,
        description="Отображаемое имя категории (не UUID), напр. «Продукты › Молочное»",
    )
    items_count: int = Field(default=0, description="Число позиций в чеке")
    items: list[TransactionItemBriefDTO] | None = Field(
        default=None, description="Позиции чека (если запрошены)"
    )


class TransactionsListResponseDTO(BaseModel):
    transactions: list[TransactionListItemDTO] = Field(description="Список транзакций")
    # Метаданные пагинации — только если передан query-параметр limit
    total: int | None = Field(
        default=None, description="Всего записей по фильтру (при пагинации)"
    )
    limit: int | None = Field(default=None, description="Размер страницы (при пагинации)")
    offset: int | None = Field(default=None, description="Смещение (при пагинации)")
    has_more: bool | None = Field(
        default=None, description="Есть ли ещё записи после текущей страницы"
    )


class CreateManualTransactionRequestDTO(BaseModel):
    account_id: str = Field(description="UUID счёта")
    type: TransactionType = Field(description="Тип: expense или income")
    amount: int = Field(gt=0, description="Сумма в копейках")
    currency: Currency = Field(default=Currency.RUB, description="Валюта")
    occurred_at: datetime = Field(description="Дата и время (локальное, без timezone)")
    category_id: str | None = Field(default=None, description="UUID категории")
    comment: str | None = Field(default=None, description="Комментарий")


class UpdateTransactionRequestDTO(BaseModel):
    amount: int | None = Field(default=None, gt=0, description="Новая сумма в копейках")
    category_id: str | None = Field(default=None, description="UUID категории")
    comment: str | None = Field(default=None, description="Новый комментарий")


class TransactionDetailDTO(BaseModel):
    id: str = Field(description="UUID транзакции")
    amount: int = Field(description="Сумма в копейках")
    source: str = Field(description="Источник: manual, qr_receipt, …")
    type: str | None = Field(default=None, description="Тип: expense или income")
    currency: str | None = Field(default=None, description="Валюта")
    occurred_at: datetime | None = Field(default=None, description="Дата и время")
    comment: str | None = Field(default=None, description="Комментарий")
    merchant: MerchantBriefDTO | None = Field(default=None, description="Магазин")
    items: list[TransactionItemBriefDTO] | None = Field(default=None, description="Позиции чека")


class TransactionResponseDTO(BaseModel):
    transaction: TransactionDetailDTO = Field(description="Транзакция")


class TransactionFilterDTO(BaseModel):
    user_id: int
    from_date: datetime | None = None
    to_date: datetime | None = None
    type: TransactionType | None = None
    account_uid: str | None = None
    timezone: str = "Europe/Moscow"
    limit: int | None = None
    offset: int = 0


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
    category_id: str = Field(description="UUID новой категории для позиции")


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
