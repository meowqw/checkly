"""Правила редактирования: QR нельзя PATCH целиком, позицию — можно."""
from sqlalchemy.orm import Session

from app.core.enums import TransactionSource
from app.core.uuid_utils import new_uid
from app.database.models import Account, Category, Product, User
from app.dto.transactions import UpdateTransactionItemDTO
from app.repositories.user_product_override_repository import UserProductCategoryOverrideRepository
from app.services.transaction_service import TransactionService
from tests.conftest import make_qr_tx


def test_update_qr_item_category(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    qr = make_qr_tx(
        db,
        user=user,
        account=account,
        items=[("Чипсы", 150_00, system_categories["snacks"])],
    )
    item = qr.items[0]
    result = TransactionService(db).update_transaction_item(
        UpdateTransactionItemDTO(
            user_id=user.id,
            transaction_uid=qr.uid,
            item_uid=item.uid,
            category_uid=system_categories["dairy"].uid,
        )
    )
    assert result.transaction.source == TransactionSource.QR_RECEIPT.value
    assert result.transaction.items is not None
    updated = next(i for i in result.transaction.items if i.id == item.uid)
    assert updated.category_id == system_categories["dairy"].uid


def test_update_item_with_product_creates_override(
    db: Session, user: User, account: Account, system_categories: dict[str, Category]
) -> None:
    product = Product(
        uid=new_uid(),
        name="Молоко",
        normalized_name="Молоко",
        category_id=system_categories["dairy"].id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    qr = make_qr_tx(
        db,
        user=user,
        account=account,
        items=[("Молоко дом", 89_00, system_categories["dairy"])],
        product=product,
    )
    item = qr.items[0]
    TransactionService(db).update_transaction_item(
        UpdateTransactionItemDTO(
            user_id=user.id,
            transaction_uid=qr.uid,
            item_uid=item.uid,
            category_uid=system_categories["other"].uid,
        )
    )
    override_cat = UserProductCategoryOverrideRepository(db).get_category_id(user.id, product.id)
    assert override_cat == system_categories["other"].id
