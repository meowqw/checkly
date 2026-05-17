"""Сервис поиска известных товаров."""
from sqlalchemy.orm import Session

from app.database.models import Product
from app.repositories.product_repository import ProductRepository


class ProductMatchingService:
    def __init__(self, db: Session):
        self._products = ProductRepository(db)

    def find_existing_product(
        self,
        raw_name: str,
        merchant_id: int | None,
        gtin: str | None = None,
        normalized_name: str | None = None,
    ) -> Product | None:
        if gtin:
            product = self._products.find_by_gtin(gtin)
            if product:
                return product

        alias = self._products.find_alias_by_raw_name_and_merchant(raw_name, merchant_id)
        if alias and alias.product:
            return alias.product

        if normalized_name:
            alias = self._products.find_alias_by_normalized_name(normalized_name)
            if alias and alias.product:
                return alias.product

        return None
