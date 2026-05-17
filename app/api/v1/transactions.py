"""Роутер транзакций."""
from datetime import datetime

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.enums import TransactionType
from app.dto.accounts import SuccessResponseDTO
from app.dto.transactions import (
    CreateManualTransactionDTO,
    CreateManualTransactionRequestDTO,
    TransactionFilterDTO,
    TransactionResponseDTO,
    TransactionsListResponseDTO,
    UpdateTransactionDTO,
    UpdateTransactionRequestDTO,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionsListResponseDTO)
def list_transactions(
    db: DbSession,
    user: CurrentUser,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    type: TransactionType | None = None,
    account_id: str | None = None,
) -> TransactionsListResponseDTO:
    filters = TransactionFilterDTO(
        user_id=user.id,
        from_date=from_date,
        to_date=to_date,
        type=type,
        account_uid=account_id,
    )
    return TransactionService(db).list_transactions(filters)


@router.post("", response_model=TransactionResponseDTO)
def create_transaction(
    dto: CreateManualTransactionRequestDTO, db: DbSession, user: CurrentUser
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
    )
    return TransactionService(db).create_manual_transaction(service_dto)


@router.get("/{transaction_id}", response_model=TransactionResponseDTO)
def get_transaction(
    transaction_id: str, db: DbSession, user: CurrentUser
) -> TransactionResponseDTO:
    return TransactionService(db).get_transaction(user.id, transaction_id)


@router.patch("/{transaction_id}", response_model=TransactionResponseDTO)
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


@router.delete("/{transaction_id}", response_model=SuccessResponseDTO)
def delete_transaction(
    transaction_id: str, db: DbSession, user: CurrentUser
) -> SuccessResponseDTO:
    return TransactionService(db).delete_transaction(user.id, transaction_id)
