"""ProductMatchingService: GTIN → alias merchant → normalized."""
from sqlalchemy.orm import Session

from app.core.uuid_utils import new_uid
from app.database.models import Category, Merchant, Product, ProductAlias
from app.services.product_matching_service import ProductMatchingService


def test_match_by_gtin(db: Session, system_categories: dict[str, Category]) -> None:
    product = Product(
        uid=new_uid(),
        name="Молоко",
        normalized_name="Молоко",
        gtin="460111",
        category_id=system_categories["dairy"].id,
    )
    db.add(product)
    db.commit()

    found = ProductMatchingService(db).find_existing_product(
        raw_name="что угодно", merchant_id=None, gtin="460111"
    )
    assert found is not None
    assert found.id == product.id


def test_match_by_raw_alias_and_merchant(
    db: Session, system_categories: dict[str, Category]
) -> None:
    merchant = Merchant(uid=new_uid(), name="Магнит", inn="111")
    db.add(merchant)
    db.flush()
    product = Product(
        uid=new_uid(),
        name="Чипсы",
        normalized_name="Чипсы",
        category_id=system_categories["snacks"].id,
    )
    db.add(product)
    db.flush()
    db.add(
        ProductAlias(
            uid=new_uid(),
            product_id=product.id,
            merchant_id=merchant.id,
            raw_name="ЧИПСЫ LAYS 140Г",
            normalized_name="Чипсы",
            confidence=0.9,
        )
    )
    db.commit()

    found = ProductMatchingService(db).find_existing_product(
        raw_name="ЧИПСЫ LAYS 140Г", merchant_id=merchant.id
    )
    assert found is not None
    assert found.id == product.id

    assert (
        ProductMatchingService(db).find_existing_product(
            raw_name="ЧИПСЫ LAYS 140Г", merchant_id=None
        )
        is None
    )


def test_match_by_normalized_name(
    db: Session, system_categories: dict[str, Category]
) -> None:
    product = Product(
        uid=new_uid(),
        name="Вода",
        normalized_name="Вода питьевая",
        category_id=system_categories["products"].id,
    )
    db.add(product)
    db.flush()
    db.add(
        ProductAlias(
            uid=new_uid(),
            product_id=product.id,
            merchant_id=None,
            raw_name="ВОДА 1.5",
            normalized_name="Вода питьевая",
            confidence=0.8,
        )
    )
    db.commit()

    found = ProductMatchingService(db).find_existing_product(
        raw_name="другое",
        merchant_id=None,
        normalized_name="Вода питьевая",
    )
    assert found is not None
    assert found.id == product.id


def test_no_match(db: Session) -> None:
    assert (
        ProductMatchingService(db).find_existing_product(
            raw_name="неизвестно", merchant_id=1, gtin=None
        )
        is None
    )
