"""Репозиторий транзакций."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.models import Account, Category, Transaction, TransactionItem, UserAccount


class TransactionRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_uid_for_user(self, uid: str, user_id: int) -> Transaction | None:
        return self._db.scalar(
            select(Transaction)
            .options(
                joinedload(Transaction.merchant),
                joinedload(Transaction.items)
                .joinedload(TransactionItem.category)
                .joinedload(Category.parent),
                joinedload(Transaction.items).joinedload(TransactionItem.product),
            )
            .where(Transaction.uid == uid, Transaction.user_id == user_id)
        )

    def list_for_user(
        self,
        user_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        transaction_type: str | None = None,
        account_id: int | None = None,
    ) -> list[Transaction]:
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        if from_date:
            stmt = stmt.where(Transaction.occurred_at >= from_date)
        if to_date:
            stmt = stmt.where(Transaction.occurred_at <= to_date)
        if transaction_type:
            stmt = stmt.where(Transaction.type == transaction_type)
        if account_id:
            stmt = stmt.where(Transaction.account_id == account_id)
        stmt = (
            stmt.options(
                joinedload(Transaction.account),
                joinedload(Transaction.merchant),
                joinedload(Transaction.items)
                .joinedload(TransactionItem.category)
                .joinedload(Category.parent),
            )
            .order_by(Transaction.occurred_at.desc())
        )
        return list(self._db.scalars(stmt).unique().all())

    def get_item_by_uid_for_user(
        self, item_uid: str, transaction_uid: str, user_id: int
    ) -> TransactionItem | None:
        return self._db.scalar(
            select(TransactionItem)
            .join(Transaction, Transaction.id == TransactionItem.transaction_id)
            .options(
                joinedload(TransactionItem.category).joinedload(Category.parent),
                joinedload(TransactionItem.product),
            )
            .where(
                TransactionItem.uid == item_uid,
                Transaction.uid == transaction_uid,
                Transaction.user_id == user_id,
            )
        )

    def create(self, transaction: Transaction) -> Transaction:
        self._db.add(transaction)
        self._db.flush()
        return transaction

    def create_item(self, item: TransactionItem) -> TransactionItem:
        self._db.add(item)
        self._db.flush()
        return item

    def delete(self, transaction: Transaction) -> None:
        self._db.delete(transaction)

    def get_account_id_by_uid(self, account_uid: str, user_id: int) -> int | None:
        stmt = (
            select(Account.id)
            .join(UserAccount, UserAccount.account_id == Account.id)
            .where(Account.uid == account_uid, UserAccount.user_id == user_id)
        )
        return self._db.scalar(stmt)
