"""Unit: маппинг item → brief с категорией и тегами."""
from types import SimpleNamespace

from app.services.transaction_mapper import map_item_to_brief


def test_map_item_category_and_tags() -> None:
    parent = SimpleNamespace(name="unused")  # не используется
    cat = SimpleNamespace(uid="cat-1", name="Продукты", color=None)
    tag = SimpleNamespace(uid="tag-1", name="Молочные")
    item = SimpleNamespace(
        uid="item-1",
        raw_name="Молоко",
        amount=100,
        category=cat,
        tags=[tag],
    )
    dto = map_item_to_brief(item)
    assert dto.category_id == "cat-1"
    assert dto.category is not None
    assert dto.category.name == "Продукты"
    assert len(dto.tags) == 1
    assert dto.tags[0].name == "Молочные"
