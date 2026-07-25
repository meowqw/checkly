"""Unit: taxonomy helpers для чеков/LLM."""
from app.core.category_taxonomy import (
    EXPENSE_TAXONOMY,
    build_taxonomy_prompt_block,
    normalize_expense_category,
    resolve_subcategory,
)


def test_normalize_expense_category_known() -> None:
    assert normalize_expense_category("Продукты") == "Продукты"
    assert normalize_expense_category("  Продукты ") == "Продукты"


def test_normalize_expense_category_unknown() -> None:
    assert normalize_expense_category("Космос") == "Прочее"
    assert normalize_expense_category(None) == "Прочее"


def test_resolve_subcategory_exact() -> None:
    assert resolve_subcategory("Продукты", "Молочные", "x") == "Молочные"


def test_resolve_subcategory_keyword_hint() -> None:
    assert resolve_subcategory("Продукты", None, "Шоколад Snickers") == "Сладости"
    assert resolve_subcategory("Продукты", None, "кефир 1%") == "Молочные"


def test_resolve_subcategory_no_children() -> None:
    assert resolve_subcategory("Подарки", "что-то", "подарок") is None


def test_build_taxonomy_prompt_contains_parents() -> None:
    block = build_taxonomy_prompt_block()
    assert "Продукты" in block
    for parent in list(EXPENSE_TAXONOMY)[:3]:
        assert parent in block
