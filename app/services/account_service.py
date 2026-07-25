"""Сервис счетов."""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import AccountMemberRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.uuid_utils import new_uid
from app.database.models import Account, AccountInvite, User
from app.dto.accounts import (
    AccountDTO,
    AccountMemberDTO,
    AccountResponseDTO,
    AccountsListResponseDTO,
    CreateAccountInviteResponseDTO,
    CreateAccountRequestDTO,
    JoinAccountRequestDTO,
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
        members_map = self._accounts.list_members_for_accounts([a.id for a in accounts])
        return AccountsListResponseDTO(
            accounts=[self._to_dto(a, members_map.get(a.id, [])) for a in accounts]
        )

    def create_account(self, user_id: int, dto: CreateAccountRequestDTO) -> AccountResponseDTO:
        account = Account(uid=new_uid(), name=dto.name, balance=dto.balance)
        self._accounts.create(account, user_id, role=AccountMemberRole.OWNER.value)
        self._db.commit()
        self._db.refresh(account)
        return AccountResponseDTO(account=self._to_dto(account, self._accounts.list_members(account.id)))

    def update_account(
        self, user_id: int, account_uid: str, dto: UpdateAccountRequestDTO
    ) -> AccountResponseDTO:
        account = self._require_owner(account_uid, user_id)
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
        return AccountResponseDTO(account=self._to_dto(account, self._accounts.list_members(account.id)))

    def delete_account(self, user_id: int, account_uid: str) -> SuccessResponseDTO:
        account = self._require_owner(account_uid, user_id)
        self._accounts.delete(account)
        self._db.commit()
        return SuccessResponseDTO()

    def create_invite(self, user_id: int, account_uid: str) -> CreateAccountInviteResponseDTO:
        account = self._require_owner(account_uid, user_id)
        invite = AccountInvite(
            uid=new_uid(),
            account_id=account.id,
            created_by_user_id=user_id,
        )
        self._accounts.create_invite(invite)
        self._db.commit()
        return CreateAccountInviteResponseDTO(token=invite.uid)

    def join_by_token(self, user_id: int, dto: JoinAccountRequestDTO) -> AccountResponseDTO:
        invite = self._accounts.get_invite_by_uid(dto.token)
        if not invite or invite.used_at is not None:
            raise NotFoundError("Приглашение не найдено")

        existing = self._accounts.get_membership(invite.account_id, user_id)
        if existing:
            raise ConflictError("Вы уже участник этого счёта")

        self._accounts.add_member(
            invite.account_id, user_id, role=AccountMemberRole.MEMBER.value
        )
        invite.used_by_user_id = user_id
        invite.used_at = datetime.utcnow()
        self._db.commit()

        account = self._db.get(Account, invite.account_id)
        if not account:
            raise NotFoundError("Счёт не найден")
        return AccountResponseDTO(account=self._to_dto(account, self._accounts.list_members(account.id)))

    def ensure_account_access(self, user_id: int, account_uid: str) -> Account:
        return self._get_user_account(account_uid, user_id)

    def _get_user_account(self, account_uid: str, user_id: int) -> Account:
        account = self._accounts.get_by_uid_for_user(account_uid, user_id)
        if not account:
            raise NotFoundError("Счёт не найден")
        return account

    def _require_owner(self, account_uid: str, user_id: int) -> Account:
        account = self._get_user_account(account_uid, user_id)
        membership = self._accounts.get_membership(account.id, user_id)
        if not membership or membership.role != AccountMemberRole.OWNER.value:
            raise ForbiddenError("Только владелец счёта может выполнить это действие")
        return account

    @staticmethod
    def _to_dto(account: Account, members: list[tuple[User, str]]) -> AccountDTO:
        return AccountDTO(
            id=account.uid,
            name=account.name,
            balance=account.balance,
            members=[
                AccountMemberDTO(id=user.uid, login=user.login, role=role)
                for user, role in members
            ],
        )
