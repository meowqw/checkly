"""Маппинг Transaction ORM → DTO для списков API."""
from app.core.category_display import category_display_name
from app.core.enums import TransactionSource
from app.database.models import Category, Transaction, TransactionItem
from app.dto.transactions import (
    AccountBriefDTO,
    CategoryBriefDTO,
    MerchantBriefDTO,
    TransactionItemBriefDTO,
    TransactionListItemDTO,
)


def map_item_to_brief(
    item: TransactionItem, category: Category | None = None
) -> TransactionItemBriefDTO:
    cat = category or item.category
    return TransactionItemBriefDTO(
        id=item.uid,
        raw_name=item.raw_name,
        amount=item.amount,
        category_id=cat.uid if cat else None,
        category=CategoryBriefDTO(name=category_display_name(cat)) if cat else None,
    )


def map_transaction_to_list_item(
    transaction: Transaction,
    *,
    compact: bool = False,
) -> TransactionListItemDTO:
    """compact=True — для виджета «последние траты»: без позиций чека, одна позиция у ручных."""
    items = transaction.items or []
    title = transaction.comment
    if not title and transaction.merchant:
        title = transaction.merchant.name
    if not title and items:
        title = items[0].raw_name
    if not title:
        title = "Операция"

    category = None
    if transaction.source != TransactionSource.QR_RECEIPT.value:
        if items and items[0].category:
            category = category_display_name(items[0].category)

    account = None
    if transaction.account:
        account = AccountBriefDTO(id=transaction.account.uid, name=transaction.account.name)

    merchant = None
    if transaction.merchant:
        merchant = MerchantBriefDTO(id=transaction.merchant.uid, name=transaction.merchant.name)

    if compact:
        if transaction.source == TransactionSource.QR_RECEIPT.value:
            item_dtos = None
        elif items:
            item_dtos = [map_item_to_brief(items[0])]
        else:
            item_dtos = None
    else:
        item_dtos = [map_item_to_brief(item) for item in items] or None

    return TransactionListItemDTO(
        id=transaction.uid,
        type=transaction.type,
        amount=transaction.amount,
        currency=transaction.currency,
        occurred_at=transaction.occurred_at,
        source=transaction.source,
        comment=transaction.comment,
        title=title,
        account=account,
        merchant=merchant,
        category=category,
        items_count=len(items),
        items=item_dtos,
    )
