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
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=AccountsListResponseDTO)
def list_accounts(db: DbSession, user: CurrentUser) -> AccountsListResponseDTO:
    return AccountService(db).list_accounts(user.id)


@router.post("", response_model=AccountResponseDTO)
def create_account(
    dto: CreateAccountRequestDTO, db: DbSession, user: CurrentUser
) -> AccountResponseDTO:
    return AccountService(db).create_account(user.id, dto)


@router.patch("/{account_id}", response_model=AccountResponseDTO)
def update_account(
    account_id: str,
    dto: UpdateAccountRequestDTO,
    db: DbSession,
    user: CurrentUser,
) -> AccountResponseDTO:
    return AccountService(db).update_account(user.id, account_id, dto)


@router.delete("/{account_id}", response_model=SuccessResponseDTO)
def delete_account(account_id: str, db: DbSession, user: CurrentUser) -> SuccessResponseDTO:
    return AccountService(db).delete_account(user.id, account_id)
