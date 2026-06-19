"""Роутер счетов."""
from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.dto.accounts import (
    AccountResponseDTO,
    AccountsListResponseDTO,
    CreateAccountRequestDTO,
    SuccessResponseDTO,
    UpdateAccountRequestDTO,
)
from app.openapi import COMMON_ERROR_RESPONSES
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])

_AUTH_ERRORS = {401: COMMON_ERROR_RESPONSES[401]}


@router.get(
    "",
    response_model=AccountsListResponseDTO,
    summary="Список счетов",
    description="Возвращает все счета текущего пользователя.",
    responses=_AUTH_ERRORS,
)
def list_accounts(db: DbSession, user: CurrentUser) -> AccountsListResponseDTO:
    return AccountService(db).list_accounts(user.id)


@router.post(
    "",
    response_model=AccountResponseDTO,
    summary="Создать счёт",
    description="Создаёт новый счёт. Баланс указывается в копейках.",
    responses={**_AUTH_ERRORS, 400: COMMON_ERROR_RESPONSES[400]},
)
def create_account(
    dto: CreateAccountRequestDTO, db: DbSession, user: CurrentUser
) -> AccountResponseDTO:
    return AccountService(db).create_account(user.id, dto)


@router.patch(
    "/{account_id}",
    response_model=AccountResponseDTO,
    summary="Обновить счёт",
    description="Частичное обновление названия и/или баланса счёта.",
    responses={**_AUTH_ERRORS, 404: COMMON_ERROR_RESPONSES[404]},
)
def update_account(
    account_id: str,
    dto: UpdateAccountRequestDTO,
    db: DbSession,
    user: CurrentUser,
) -> AccountResponseDTO:
    return AccountService(db).update_account(user.id, account_id, dto)


@router.delete(
    "/{account_id}",
    response_model=SuccessResponseDTO,
    summary="Удалить счёт",
    description="Удаляет счёт. Нельзя удалить счёт с транзакциями.",
    responses={**_AUTH_ERRORS, 404: COMMON_ERROR_RESPONSES[404], 409: COMMON_ERROR_RESPONSES[409]},
)
def delete_account(account_id: str, db: DbSession, user: CurrentUser) -> SuccessResponseDTO:
    return AccountService(db).delete_account(user.id, account_id)
