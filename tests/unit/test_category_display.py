"""Unit: отображаемые имена категорий."""
from types import SimpleNamespace

from app.core.category_display import category_display_name


def test_display_name_root() -> None:
    cat = SimpleNamespace(name="Продукты", parent=None)
    assert category_display_name(cat) == "Продукты"


def test_display_name_with_parent() -> None:
    parent = SimpleNamespace(name="Продукты", parent=None)
    child = SimpleNamespace(name="Молочные", parent=parent)
    assert category_display_name(child) == "Продукты › Молочные"


def test_display_name_none() -> None:
    assert category_display_name(None) is None
