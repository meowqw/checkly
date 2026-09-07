"""Unit: taxonomy helpers для чеков/LLM."""
from app.core.category_taxonomy import (
    EXPENSE_CATEGORIES,
    SYSTEM_TAGS,
    build_taxonomy_prompt_block,
    normalize_expense_category,
    resolve_tags,
)


def test_normalize_expense_category_known() -> None:
    assert normalize_expense_category("Продукты") == "Продукты"
    assert normalize_expense_category("  Продукты ") == "Продукты"


def test_normalize_expense_category_unknown() -> None:
    assert normalize_expense_category("Космос") == "Прочее"
    assert normalize_expense_category(None) == "Прочее"


def test_resolve_tags_exact() -> None:
    assert resolve_tags(["Молочные"], "x") == ["Молочные"]


def test_resolve_tags_keyword_hint() -> None:
    assert "Сладости" in resolve_tags(None, "Шоколад Snickers")
    assert "Молочные" in resolve_tags([], "кефир 1%")


def test_resolve_tags_ignores_unknown() -> None:
    assert resolve_tags(["Несуществующий"], "подарок") == []


def test_build_taxonomy_prompt_flat() -> None:
    block = build_taxonomy_prompt_block()
    assert "Продукты" in block
    assert "Молочные" in block
    assert "подкатегор" not in block.lower()
    for name in EXPENSE_CATEGORIES[:3]:
        assert name in block
    assert SYSTEM_TAGS[0] in block
