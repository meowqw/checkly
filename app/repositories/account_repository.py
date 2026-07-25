"""Репозиторий счетов."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AccountMemberRole
from app.database.models import Account, AccountInvite, User, UserAccount


class AccountRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_uid_for_user(self, account_uid: str, user_id: int) -> Account | None:
        stmt = (
            select(Account)
            .join(UserAccount, UserAccount.account_id == Account.id)
            .where(Account.uid == account_uid, UserAccount.user_id == user_id)
        )
        return self._db.scalar(stmt)

    def get_membership(self, account_id: int, user_id: int) -> UserAccount | None:
        return self._db.scalar(
            select(UserAccount).where(
                UserAccount.account_id == account_id,
                UserAccount.user_id == user_id,
            )
        )

    def list_for_user(self, user_id: int) -> list[Account]:
        stmt = (
            select(Account)
            .join(UserAccount, UserAccount.account_id == Account.id)
            .where(UserAccount.user_id == user_id)
            .order_by(Account.created_at.desc())
        )
        return list(self._db.scalars(stmt).all())

    def list_members(self, account_id: int) -> list[tuple[User, str]]:
        stmt = (
            select(User, UserAccount.role)
            .join(UserAccount, UserAccount.user_id == User.id)
            .where(UserAccount.account_id == account_id)
            .order_by(UserAccount.role.asc(), User.login.asc())
        )
        return [(row[0], row[1]) for row in self._db.execute(stmt).all()]

    def list_members_for_accounts(
        self, account_ids: list[int]
    ) -> dict[int, list[tuple[User, str]]]:
        if not account_ids:
            return {}
        stmt = (
            select(UserAccount.account_id, User, UserAccount.role)
            .join(User, User.id == UserAccount.user_id)
            .where(UserAccount.account_id.in_(account_ids))
            .order_by(UserAccount.role.asc(), User.login.asc())
        )
        result: dict[int, list[tuple[User, str]]] = {aid: [] for aid in account_ids}
        for account_id, user, role in self._db.execute(stmt).all():
            result[account_id].append((user, role))
        return result

    def create(
        self,
        account: Account,
        user_id: int,
        *,
        role: str = AccountMemberRole.OWNER.value,
    ) -> Account:
        self._db.add(account)
        self._db.flush()
        self._db.add(UserAccount(user_id=user_id, account_id=account.id, role=role))
        self._db.flush()
        return account

    def add_member(
        self,
        account_id: int,
        user_id: int,
        *,
        role: str = AccountMemberRole.MEMBER.value,
    ) -> UserAccount:
        link = UserAccount(user_id=user_id, account_id=account_id, role=role)
        self._db.add(link)
        self._db.flush()
        return link

    def delete(self, account: Account) -> None:
        self._db.delete(account)

    def create_invite(self, invite: AccountInvite) -> AccountInvite:
        self._db.add(invite)
        self._db.flush()
        return invite

    def get_invite_by_uid(self, token: str) -> AccountInvite | None:
        return self._db.scalar(select(AccountInvite).where(AccountInvite.uid == token))
