"""Сервис счетов."""
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.uuid_utils import new_uid
from app.database.models import Account
from app.dto.accounts import (
    AccountDTO,
    AccountResponseDTO,
    AccountsListResponseDTO,
    CreateAccountRequestDTO,
    SuccessResponseDTO,
    UpdateAccountRequestDTO,
)
from app.repositories.account_repository import AccountRepository

logger = logging.getLogger(__name__)


class AccountService:
    def __init__(self, db: Session):
        self._accounts = AccountRepository(db)
        self._db = db

    def list_accounts(self, user_id: int) -> AccountsListResponseDTO:
        accounts = self._accounts.list_for_user(user_id)
        return AccountsListResponseDTO(
            accounts=[AccountDTO(id=a.uid, name=a.name, balance=a.balance) for a in accounts]
        )

    def create_account(self, user_id: int, dto: CreateAccountRequestDTO) -> AccountResponseDTO:
        account = Account(uid=new_uid(), name=dto.name, balance=dto.balance)
        self._accounts.create(account, user_id)
        self._db.commit()
        self._db.refresh(account)
        return AccountResponseDTO(account=AccountDTO(id=account.uid, name=account.name, balance=account.balance))

    def update_account(
        self, user_id: int, account_uid: str, dto: UpdateAccountRequestDTO
    ) -> AccountResponseDTO:
        account = self._get_user_account(account_uid, user_id)
        if dto.name is not None:
            account.name = dto.name
        if dto.balance is not None:
            logger.warning(
                "Прямое изменение balance счёта %s — лучше корректировать через транзакции",
                account.uid,
            )
            account.balance = dto.balance
        self._db.commit()
        self._db.refresh(account)
        return AccountResponseDTO(account=AccountDTO(id=account.uid, name=account.name, balance=account.balance))

    def delete_account(self, user_id: int, account_uid: str) -> SuccessResponseDTO:
        account = self._get_user_account(account_uid, user_id)
        self._accounts.delete(account)
        self._db.commit()
        return SuccessResponseDTO()

    def _get_user_account(self, account_uid: str, user_id: int) -> Account:
        account = self._accounts.get_by_uid_for_user(account_uid, user_id)
        if not account:
            raise NotFoundError("Счёт не найден")
        return account

    def ensure_account_access(self, user_id: int, account_uid: str) -> Account:
        account = self._get_user_account(account_uid, user_id)
        return account
