"""Репозиторий персональных категорий товаров."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import UserProductCategoryOverride


class UserProductCategoryOverrideRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_category_id(self, user_id: int, product_id: int) -> int | None:
        return self._db.scalar(
            select(UserProductCategoryOverride.category_id).where(
                UserProductCategoryOverride.user_id == user_id,
                UserProductCategoryOverride.product_id == product_id,
            )
        )

    def get_category_ids_for_products(
        self, user_id: int, product_ids: list[int]
    ) -> dict[int, int]:
        if not product_ids:
            return {}
        rows = self._db.execute(
            select(
                UserProductCategoryOverride.product_id,
                UserProductCategoryOverride.category_id,
            ).where(
                UserProductCategoryOverride.user_id == user_id,
                UserProductCategoryOverride.product_id.in_(product_ids),
            )
        ).all()
        return {product_id: category_id for product_id, category_id in rows}

    def upsert(self, user_id: int, product_id: int, category_id: int) -> None:
        row = self._db.scalar(
            select(UserProductCategoryOverride).where(
                UserProductCategoryOverride.user_id == user_id,
                UserProductCategoryOverride.product_id == product_id,
            )
        )
        if row:
            row.category_id = category_id
            return
        self._db.add(
            UserProductCategoryOverride(
                user_id=user_id,
                product_id=product_id,
                category_id=category_id,
            )
        )
