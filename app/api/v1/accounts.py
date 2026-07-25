"""Роутер счетов."""
from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.dto.accounts import (
    AccountResponseDTO,
    AccountsListResponseDTO,
    CreateAccountInviteResponseDTO,
    CreateAccountRequestDTO,
    JoinAccountRequestDTO,
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
    description="Возвращает все счета текущего пользователя, включая общие, с участниками.",
    responses=_AUTH_ERRORS,
)
def list_accounts(db: DbSession, user: CurrentUser) -> AccountsListResponseDTO:
    return AccountService(db).list_accounts(user.id)


@router.post(
    "",
    response_model=AccountResponseDTO,
    summary="Создать счёт",
    description="Создаёт новый счёт. Баланс указывается в копейках. Создатель становится владельцем.",
    responses={**_AUTH_ERRORS, 400: COMMON_ERROR_RESPONSES[400]},
)
def create_account(
    dto: CreateAccountRequestDTO, db: DbSession, user: CurrentUser
) -> AccountResponseDTO:
    return AccountService(db).create_account(user.id, dto)


@router.post(
    "/join",
    response_model=AccountResponseDTO,
    summary="Принять приглашение на счёт",
    description="Одноразовый токен. После успешного join счёт появляется у пользователя как общий.",
    responses={
        **_AUTH_ERRORS,
        404: COMMON_ERROR_RESPONSES[404],
        409: COMMON_ERROR_RESPONSES[409],
    },
)
def join_account(
    dto: JoinAccountRequestDTO, db: DbSession, user: CurrentUser
) -> AccountResponseDTO:
    return AccountService(db).join_by_token(user.id, dto)


@router.post(
    "/{account_id}/invites",
    response_model=CreateAccountInviteResponseDTO,
    summary="Создать приглашение на счёт",
    description="Только владелец. Возвращает одноразовый токен для передачи другому пользователю.",
    responses={
        **_AUTH_ERRORS,
        403: COMMON_ERROR_RESPONSES[403],
        404: COMMON_ERROR_RESPONSES[404],
    },
)
def create_account_invite(
    account_id: str, db: DbSession, user: CurrentUser
) -> CreateAccountInviteResponseDTO:
    return AccountService(db).create_invite(user.id, account_id)


@router.patch(
    "/{account_id}",
    response_model=AccountResponseDTO,
    summary="Обновить счёт",
    description="Частичное обновление названия и/или баланса. Только владелец.",
    responses={
        **_AUTH_ERRORS,
        403: COMMON_ERROR_RESPONSES[403],
        404: COMMON_ERROR_RESPONSES[404],
    },
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
    description="Удаляет счёт. Только владелец. Нельзя удалить счёт с транзакциями.",
    responses={
        **_AUTH_ERRORS,
        403: COMMON_ERROR_RESPONSES[403],
        404: COMMON_ERROR_RESPONSES[404],
        409: COMMON_ERROR_RESPONSES[409],
    },
)
def delete_account(account_id: str, db: DbSession, user: CurrentUser) -> SuccessResponseDTO:
    return AccountService(db).delete_account(user.id, account_id)
