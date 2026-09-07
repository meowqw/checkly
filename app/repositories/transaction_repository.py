"""Репозиторий транзакций."""
from datetime import datetime
from typing import Any

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import ColumnElement

from app.core.enums import TransactionType
from app.database.models import (
    Account,
    Category,
    Transaction,
    TransactionItem,
    TransactionItemTag,
    UserAccount,
)


class TransactionRepository:
    def __init__(self, db: Session):
        self._db = db

    @staticmethod
    def _accessible_account_ids(user_id: int) -> ColumnElement[bool]:
        """Доступ ко всем транзакциям на счетах пользователя (включая общие)."""
        return Transaction.account_id.in_(
            select(UserAccount.account_id).where(UserAccount.user_id == user_id)
        )

    @staticmethod
    def _item_match_exists(
        *,
        category_ids: list[int] | None = None,
        tag_ids: list[int] | None = None,
    ):
        """EXISTS позиция транзакции, удовлетворяющая фильтрам category/tag."""
        conds = [TransactionItem.transaction_id == Transaction.id]
        if category_ids is not None:
            conds.append(TransactionItem.category_id.in_(category_ids))
        if tag_ids is not None:
            conds.append(
                exists(
                    select(TransactionItemTag.item_id).where(
                        TransactionItemTag.item_id == TransactionItem.id,
                        TransactionItemTag.tag_id.in_(tag_ids),
                    )
                )
            )
        return exists(select(TransactionItem.id).where(*conds))

    def _apply_item_filters(
        self,
        stmt: Any,
        *,
        category_ids: list[int] | None = None,
        tag_ids: list[int] | None = None,
    ) -> Any:
        if category_ids is None and tag_ids is None:
            return stmt
        return stmt.where(
            self._item_match_exists(category_ids=category_ids, tag_ids=tag_ids)
        )

    @staticmethod
    def _tx_list_options():
        return (
            selectinload(Transaction.account),
            selectinload(Transaction.merchant),
            selectinload(Transaction.items).selectinload(TransactionItem.category),
            selectinload(Transaction.items).selectinload(TransactionItem.tags),
        )

    def get_by_uid_for_user(self, uid: str, user_id: int) -> Transaction | None:
        return self._db.scalar(
            select(Transaction)
            .options(
                selectinload(Transaction.merchant),
                selectinload(Transaction.items).selectinload(TransactionItem.category),
                selectinload(Transaction.items).selectinload(TransactionItem.tags),
                selectinload(Transaction.items).selectinload(TransactionItem.product),
            )
            .where(Transaction.uid == uid, self._accessible_account_ids(user_id))
        )

    def list_for_user(
        self,
        user_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        transaction_type: str | None = None,
        account_id: int | None = None,
        category_ids: list[int] | None = None,
        tag_ids: list[int] | None = None,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Transaction]:
        stmt = select(Transaction).where(self._accessible_account_ids(user_id))
        stmt = self._apply_filters(
            stmt,
            from_date=from_date,
            to_date=to_date,
            transaction_type=transaction_type,
            account_id=account_id,
        )
        stmt = self._apply_item_filters(stmt, category_ids=category_ids, tag_ids=tag_ids)
        stmt = stmt.options(*self._tx_list_options()).order_by(Transaction.occurred_at.desc())
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self._db.scalars(stmt).all())

    def count_for_user(
        self,
        user_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        transaction_type: str | None = None,
        account_id: int | None = None,
        category_ids: list[int] | None = None,
        tag_ids: list[int] | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Transaction)
            .where(self._accessible_account_ids(user_id))
        )
        stmt = self._apply_filters(
            stmt,
            from_date=from_date,
            to_date=to_date,
            transaction_type=transaction_type,
            account_id=account_id,
        )
        stmt = self._apply_item_filters(stmt, category_ids=category_ids, tag_ids=tag_ids)
        return int(self._db.scalar(stmt) or 0)

    def list_recent_expenses(
        self,
        user_id: int,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        account_id: int | None = None,
        category_ids: list[int] | None = None,
        tag_ids: list[int] | None = None,
        limit: int = 8,
    ) -> list[Transaction]:
        stmt = select(Transaction).where(
            self._accessible_account_ids(user_id),
            Transaction.type == TransactionType.EXPENSE.value,
        )
        stmt = self._apply_filters(
            stmt,
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
        )
        stmt = self._apply_item_filters(stmt, category_ids=category_ids, tag_ids=tag_ids)
        stmt = (
            stmt.options(*self._tx_list_options())
            .order_by(Transaction.occurred_at.desc())
            .limit(limit)
        )
        return list(self._db.scalars(stmt).all())

    def sum_amounts_by_type(
        self,
        user_id: int,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        account_id: int | None = None,
    ) -> dict[str, int]:
        stmt = (
            select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
            .where(self._accessible_account_ids(user_id))
        )
        stmt = self._apply_filters(
            stmt,
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
        )
        stmt = stmt.group_by(Transaction.type)
        return {row[0]: int(row[1]) for row in self._db.execute(stmt).all()}

    def sum_item_amounts_by_type(
        self,
        user_id: int,
        *,
        category_ids: list[int] | None = None,
        tag_ids: list[int] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        account_id: int | None = None,
    ) -> dict[str, int]:
        """Суммы по типу транзакции по позициям, попадающим в category/tag фильтр."""
        if category_ids is None and tag_ids is None:
            return {}
        stmt = (
            select(Transaction.type, func.coalesce(func.sum(TransactionItem.amount), 0))
            .join(Transaction, Transaction.id == TransactionItem.transaction_id)
            .where(self._accessible_account_ids(user_id))
        )
        if category_ids is not None:
            stmt = stmt.where(TransactionItem.category_id.in_(category_ids))
        if tag_ids is not None:
            stmt = stmt.where(
                exists(
                    select(TransactionItemTag.item_id).where(
                        TransactionItemTag.item_id == TransactionItem.id,
                        TransactionItemTag.tag_id.in_(tag_ids),
                    )
                )
            )
        stmt = self._apply_filters(
            stmt,
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
            model=Transaction,
        )
        stmt = stmt.group_by(Transaction.type)
        return {row[0]: int(row[1]) for row in self._db.execute(stmt).all()}

    def aggregate_expense_category_amounts(
        self,
        user_id: int,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        account_id: int | None = None,
        category_ids: list[int] | None = None,
        tag_ids: list[int] | None = None,
    ) -> list[tuple[int | None, int]]:
        """Суммы расходов по category_id (None = «Прочее»)."""
        totals: dict[int | None, int] = {}

        items_stmt = (
            select(
                TransactionItem.category_id,
                func.coalesce(func.sum(TransactionItem.amount), 0),
            )
            .join(Transaction, Transaction.id == TransactionItem.transaction_id)
            .where(
                self._accessible_account_ids(user_id),
                Transaction.type == TransactionType.EXPENSE.value,
            )
        )
        if category_ids is not None:
            items_stmt = items_stmt.where(TransactionItem.category_id.in_(category_ids))
        if tag_ids is not None:
            items_stmt = items_stmt.where(
                exists(
                    select(TransactionItemTag.item_id).where(
                        TransactionItemTag.item_id == TransactionItem.id,
                        TransactionItemTag.tag_id.in_(tag_ids),
                    )
                )
            )
        items_stmt = self._apply_filters(
            items_stmt,
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
            model=Transaction,
        )
        items_stmt = items_stmt.group_by(TransactionItem.category_id)
        for category_id, amount in self._db.execute(items_stmt).all():
            totals[category_id] = totals.get(category_id, 0) + int(amount)

        # «Прочее» без позиций — только без category/tag фильтра
        if category_ids is None and tag_ids is None:
            has_items = exists(
                select(TransactionItem.id).where(
                    TransactionItem.transaction_id == Transaction.id
                )
            )
            orphan_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                self._accessible_account_ids(user_id),
                Transaction.type == TransactionType.EXPENSE.value,
                ~has_items,
            )
            orphan_stmt = self._apply_filters(
                orphan_stmt,
                from_date=from_date,
                to_date=to_date,
                account_id=account_id,
            )
            orphan_amount = int(self._db.scalar(orphan_stmt) or 0)
            if orphan_amount:
                totals[None] = totals.get(None, 0) + orphan_amount

        return list(totals.items())

    def get_categories_by_ids(self, category_ids: list[int]) -> dict[int, Category]:
        if not category_ids:
            return {}
        stmt = select(Category).where(Category.id.in_(category_ids))
        return {c.id: c for c in self._db.scalars(stmt).all()}

    def get_item_by_uid_for_user(
        self, item_uid: str, transaction_uid: str, user_id: int
    ) -> TransactionItem | None:
        return self._db.scalar(
            select(TransactionItem)
            .join(Transaction, Transaction.id == TransactionItem.transaction_id)
            .options(
                selectinload(TransactionItem.category),
                selectinload(TransactionItem.tags),
                selectinload(TransactionItem.product),
            )
            .where(
                TransactionItem.uid == item_uid,
                Transaction.uid == transaction_uid,
                self._accessible_account_ids(user_id),
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

    @staticmethod
    def _apply_filters(
        stmt: Any,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        transaction_type: str | None = None,
        account_id: int | None = None,
        model: type = Transaction,
    ) -> Any:
        if from_date is not None:
            stmt = stmt.where(model.occurred_at >= from_date)
        if to_date is not None:
            stmt = stmt.where(model.occurred_at <= to_date)
        if transaction_type is not None:
            stmt = stmt.where(model.type == transaction_type)
        if account_id is not None:
            stmt = stmt.where(model.account_id == account_id)
        return stmt
