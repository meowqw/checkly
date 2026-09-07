"""Unit: отображаемое имя категории."""
from types import SimpleNamespace

from app.core.category_display import category_display_name


def test_category_display_name_flat() -> None:
    cat = SimpleNamespace(name="Продукты")
    assert category_display_name(cat) == "Продукты"


def test_category_display_name_none() -> None:
    assert category_display_name(None) is None
