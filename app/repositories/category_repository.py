"""Репозиторий категорий (плоские)."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.models import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_uid(self, uid: str) -> Category | None:
        return self._db.scalar(select(Category).where(Category.uid == uid))

    def get_by_uid_for_user(self, uid: str, user_id: int) -> Category | None:
        stmt = select(Category).where(
            Category.uid == uid,
            or_(Category.user_id.is_(None), Category.user_id == user_id),
        )
        return self._db.scalar(stmt)

    def get_user_category(self, uid: str, user_id: int) -> Category | None:
        return self._db.scalar(
            select(Category).where(Category.uid == uid, Category.user_id == user_id)
        )

    def list_for_user(self, user_id: int) -> list[Category]:
        stmt = (
            select(Category)
            .where(or_(Category.user_id.is_(None), Category.user_id == user_id))
            .order_by(Category.type, Category.name)
        )
        return list(self._db.scalars(stmt).all())

    def find_system_by_name_and_type(self, name: str, category_type: str) -> Category | None:
        stmt = select(Category).where(
            Category.user_id.is_(None),
            Category.name == name,
            Category.type == category_type,
        )
        return self._db.scalar(stmt)

    def find_visible_by_name(
        self,
        user_id: int,
        name: str,
        category_type: str,
        *,
        exclude_id: int | None = None,
    ) -> Category | None:
        """Системная или своя категория с тем же именем и типом."""
        stmt = select(Category).where(
            or_(Category.user_id.is_(None), Category.user_id == user_id),
            Category.name == name,
            Category.type == category_type,
        )
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        return self._db.scalar(stmt)

    def create(self, category: Category) -> Category:
        self._db.add(category)
        self._db.flush()
        return category

    def delete(self, category: Category) -> None:
        self._db.delete(category)
