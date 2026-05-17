"""Репозиторий товаров и алиасов."""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.models import Product, ProductAlias


class ProductRepository:
    def __init__(self, db: Session):
        self._db = db

    def find_by_gtin(self, gtin: str) -> Product | None:
        return self._db.scalar(
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.gtin == gtin)
        )

    def find_alias_by_raw_name_and_merchant(
        self, raw_name: str, merchant_id: int | None
    ) -> ProductAlias | None:
        stmt = (
            select(ProductAlias)
            .options(joinedload(ProductAlias.product).joinedload(Product.category))
            .where(ProductAlias.raw_name == raw_name)
        )
        if merchant_id is not None:
            stmt = stmt.where(ProductAlias.merchant_id == merchant_id)
        else:
            stmt = stmt.where(ProductAlias.merchant_id.is_(None))
        return self._db.scalar(stmt)

    def find_alias_by_normalized_name(self, normalized_name: str) -> ProductAlias | None:
        return self._db.scalar(
            select(ProductAlias)
            .options(joinedload(ProductAlias.product).joinedload(Product.category))
            .where(ProductAlias.normalized_name == normalized_name)
            .order_by(ProductAlias.confidence.desc().nullslast())
        )

    def create_product(self, product: Product) -> Product:
        self._db.add(product)
        self._db.flush()
        return product

    def create_alias(self, alias: ProductAlias) -> ProductAlias:
        self._db.add(alias)
        self._db.flush()
        return alias
