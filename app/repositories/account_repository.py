"""Репозиторий счетов."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Account, UserAccount


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

    def list_for_user(self, user_id: int) -> list[Account]:
        stmt = (
            select(Account)
            .join(UserAccount, UserAccount.account_id == Account.id)
            .where(UserAccount.user_id == user_id)
            .order_by(Account.created_at.desc())
        )
        return list(self._db.scalars(stmt).all())

    def create(self, account: Account, user_id: int) -> Account:
        self._db.add(account)
        self._db.flush()
        self._db.add(UserAccount(user_id=user_id, account_id=account.id))
        self._db.flush()
        return account

    def delete(self, account: Account) -> None:
        self._db.delete(account)
