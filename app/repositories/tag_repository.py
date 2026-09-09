"""Репозиторий тегов."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.models import Tag, Transaction, TransactionItem, TransactionItemTag


class TagRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_uid_for_user(self, uid: str, user_id: int) -> Tag | None:
        stmt = select(Tag).where(
            Tag.uid == uid,
            or_(Tag.user_id.is_(None), Tag.user_id == user_id),
        )
        return self._db.scalar(stmt)

    def get_user_tag(self, uid: str, user_id: int) -> Tag | None:
        return self._db.scalar(select(Tag).where(Tag.uid == uid, Tag.user_id == user_id))

    def list_for_user(self, user_id: int) -> list[tuple[Tag, int]]:
        """Системные + свои теги; usage_count по позициям пользователя; чаще используемые выше."""
        usage_subq = (
            select(
                TransactionItemTag.tag_id.label("tag_id"),
                func.count().label("usage_count"),
            )
            .join(TransactionItem, TransactionItem.id == TransactionItemTag.item_id)
            .join(Transaction, Transaction.id == TransactionItem.transaction_id)
            .where(Transaction.user_id == user_id)
            .group_by(TransactionItemTag.tag_id)
            .subquery()
        )
        usage_count = func.coalesce(usage_subq.c.usage_count, 0)
        stmt = (
            select(Tag, usage_count)
            .outerjoin(usage_subq, usage_subq.c.tag_id == Tag.id)
            .where(or_(Tag.user_id.is_(None), Tag.user_id == user_id))
            .order_by(usage_count.desc(), Tag.name)
        )
        return [(row[0], int(row[1])) for row in self._db.execute(stmt).all()]

    def find_system_by_name(self, name: str) -> Tag | None:
        return self._db.scalar(
            select(Tag).where(Tag.user_id.is_(None), Tag.name == name)
        )

    def find_visible_by_name(
        self,
        user_id: int,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> Tag | None:
        stmt = select(Tag).where(
            or_(Tag.user_id.is_(None), Tag.user_id == user_id),
            Tag.name == name,
        )
        if exclude_id is not None:
            stmt = stmt.where(Tag.id != exclude_id)
        return self._db.scalar(stmt)

    def find_system_by_names(self, names: list[str]) -> list[Tag]:
        if not names:
            return []
        return list(
            self._db.scalars(
                select(Tag).where(Tag.user_id.is_(None), Tag.name.in_(names))
            ).all()
        )

    def create(self, tag: Tag) -> Tag:
        self._db.add(tag)
        self._db.flush()
        return tag

    def delete(self, tag: Tag) -> None:
        self._db.delete(tag)
