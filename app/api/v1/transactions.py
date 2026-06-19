"""Роутер транзакций."""
from datetime import datetime

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, UserTimezone
from app.core.enums import TransactionType
from app.dto.accounts import SuccessResponseDTO
from app.dto.transactions import (
    CreateManualTransactionDTO,
    CreateManualTransactionRequestDTO,
    TransactionFilterDTO,
    TransactionResponseDTO,
    TransactionsListResponseDTO,
    UpdateTransactionDTO,
    UpdateTransactionItemDTO,
    UpdateTransactionItemRequestDTO,
    UpdateTransactionRequestDTO,
)
from app.openapi import COMMON_ERROR_RESPONSES
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])

_AUTH_ERRORS = {401: COMMON_ERROR_RESPONSES[401]}


@router.get(
    "",
    response_model=TransactionsListResponseDTO,
    summary="Список транзакций",
    description=(
        "Фильтрация по периоду (`from`, `to` — даты YYYY-MM-DD в часовом поясе клиента), "
        "типу и счёту. В списке есть поля title, account, category (отображаемое имя)."
    ),
    responses=_AUTH_ERRORS,
)
def list_transactions(
    db: DbSession,
    user: CurrentUser,
    tz: UserTimezone,
    from_date: datetime | None = Query(
        default=None,
        alias="from",
        description="Начало периода (YYYY-MM-DD), включительно",
    ),
    to_date: datetime | None = Query(
        default=None,
        alias="to",
        description="Конец периода (YYYY-MM-DD), включительно",
    ),
    type: TransactionType | None = Query(default=None, description="Фильтр: expense или income"),
    account_id: str | None = Query(default=None, description="UUID счёта"),
) -> TransactionsListResponseDTO:
    filters = TransactionFilterDTO(
        user_id=user.id,
        from_date=from_date,
        to_date=to_date,
        type=type,
        account_uid=account_id,
        timezone=tz,
    )
    return TransactionService(db).list_transactions(filters)


@router.post(
    "",
    response_model=TransactionResponseDTO,
    summary="Создать транзакцию",
    description="Ручная запись дохода или расхода. Сумма — в копейках.",
    responses={**_AUTH_ERRORS, 400: COMMON_ERROR_RESPONSES[400], 404: COMMON_ERROR_RESPONSES[404]},
)
def create_transaction(
    dto: CreateManualTransactionRequestDTO, db: DbSession, user: CurrentUser, tz: UserTimezone
) -> TransactionResponseDTO:
    service_dto = CreateManualTransactionDTO(
        user_id=user.id,
        account_uid=dto.account_id,
        type=dto.type,
        amount=dto.amount,
        currency=dto.currency,
        occurred_at=dto.occurred_at,
        category_uid=dto.category_id,
        comment=dto.comment,
        timezone=tz,
    )
    return TransactionService(db).create_manual_transaction(service_dto)


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponseDTO,
    summary="Детали транзакции",
    description="Полная транзакция с позициями чека (если есть). Без полей title/account из списка.",
    responses={**_AUTH_ERRORS, 404: COMMON_ERROR_RESPONSES[404]},
)
def get_transaction(
    transaction_id: str, db: DbSession, user: CurrentUser
) -> TransactionResponseDTO:
    return TransactionService(db).get_transaction(user.id, transaction_id)


@router.patch(
    "/{transaction_id}",
    response_model=TransactionResponseDTO,
    summary="Обновить транзакцию",
    description="Изменение суммы, категории или комментария ручной транзакции.",
    responses={**_AUTH_ERRORS, 404: COMMON_ERROR_RESPONSES[404]},
)
def update_transaction(
    transaction_id: str,
    dto: UpdateTransactionRequestDTO,
    db: DbSession,
    user: CurrentUser,
) -> TransactionResponseDTO:
    service_dto = UpdateTransactionDTO(
        user_id=user.id,
        transaction_uid=transaction_id,
        amount=dto.amount,
        category_uid=dto.category_id,
        comment=dto.comment,
    )
    return TransactionService(db).update_transaction(service_dto)


@router.patch(
    "/{transaction_id}/items/{item_id}",
    response_model=TransactionResponseDTO,
    summary="Категория позиции чека",
    description="Назначает категорию отдельной позиции в чеке.",
    responses={**_AUTH_ERRORS, 404: COMMON_ERROR_RESPONSES[404]},
)
def update_transaction_item(
    transaction_id: str,
    item_id: str,
    dto: UpdateTransactionItemRequestDTO,
    db: DbSession,
    user: CurrentUser,
) -> TransactionResponseDTO:
    service_dto = UpdateTransactionItemDTO(
        user_id=user.id,
        transaction_uid=transaction_id,
        item_uid=item_id,
        category_uid=dto.category_id,
    )
    return TransactionService(db).update_transaction_item(service_dto)


@router.delete(
    "/{transaction_id}",
    response_model=SuccessResponseDTO,
    summary="Удалить транзакцию",
    description="Удаляет транзакцию и откатывает изменение баланса счёта.",
    responses={**_AUTH_ERRORS, 404: COMMON_ERROR_RESPONSES[404]},
)
def delete_transaction(
    transaction_id: str, db: DbSession, user: CurrentUser
) -> SuccessResponseDTO:
    return TransactionService(db).delete_transaction(user.id, transaction_id)
