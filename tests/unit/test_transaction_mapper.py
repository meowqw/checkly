"""Unit: transaction_mapper compact / QR category null."""
from datetime import datetime
from types import SimpleNamespace

from app.core.enums import TransactionSource, TransactionType
from app.services.transaction_mapper import map_transaction_to_list_item


def _tx(**kwargs):
    defaults = dict(
        uid="tx-1",
        type=TransactionType.EXPENSE.value,
        amount=100_00,
        currency="RUB",
        occurred_at=datetime(2026, 6, 1, 12, 0, 0),
        source=TransactionSource.MANUAL.value,
        comment="Коммент",
        account=SimpleNamespace(uid="acc-1", name="Карта"),
        merchant=None,
        items=[],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_manual_list_item_has_category_and_items() -> None:
    parent = SimpleNamespace(name="Продукты", parent=None, color="#16a34a")
    cat = SimpleNamespace(uid="cat-1", name="Молочные", parent=parent, color=None)
    item = SimpleNamespace(
        uid="item-1",
        raw_name="Молоко",
        amount=100_00,
        category=cat,
    )
    dto = map_transaction_to_list_item(_tx(items=[item]))
    assert dto.category == "Продукты › Молочные"
    assert dto.items_count == 1
    assert dto.items is not None
    assert dto.items[0].category_id == "cat-1"
    assert dto.title == "Коммент"


def test_qr_list_item_category_null_but_items_present() -> None:
    cat = SimpleNamespace(uid="c", name="Снэки", parent=SimpleNamespace(name="Продукты", parent=None), color=None)
    item = SimpleNamespace(uid="i", raw_name="Чипсы", amount=50_00, category=cat)
    merchant = SimpleNamespace(uid="m", name="Пятёрочка")
    dto = map_transaction_to_list_item(
        _tx(
            source=TransactionSource.QR_RECEIPT.value,
            comment=None,
            merchant=merchant,
            items=[item],
        )
    )
    assert dto.category is None
    assert dto.title == "Пятёрочка"
    assert dto.items is not None
    assert len(dto.items) == 1


def test_compact_qr_hides_items() -> None:
    item = SimpleNamespace(uid="i", raw_name="X", amount=10, category=None)
    dto = map_transaction_to_list_item(
        _tx(source=TransactionSource.QR_RECEIPT.value, comment=None, items=[item]),
        compact=True,
    )
    assert dto.items is None
    assert dto.items_count == 1
    assert dto.title == "X"


def test_fallback_title() -> None:
    dto = map_transaction_to_list_item(_tx(comment=None, merchant=None, items=[]))
    assert dto.title == "Операция"
