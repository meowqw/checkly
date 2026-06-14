"""Сидер системных категорий расходов и доходов."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.category_taxonomy import (
    EXPENSE_CATEGORY_META,
    EXPENSE_TAXONOMY,
    INCOME_CATEGORY_META,
)
from app.core.enums import CategoryType
from app.core.uuid_utils import new_uid
from app.database import SessionLocal
from app.database.models import Category
from app.repositories.category_repository import CategoryRepository

EXPENSE_CATEGORIES = EXPENSE_TAXONOMY

INCOME_CATEGORIES = {
    "Зарплата": [],
    "Подработка": [],
    "Возвраты": [],
    "Прочие доходы": [],
}


def _meta_for(name: str, category_type: str, parent_id: int | None) -> dict[str, str]:
    if parent_id is not None:
        return {}
    if category_type == CategoryType.EXPENSE.value:
        return EXPENSE_CATEGORY_META.get(name, {})
    return INCOME_CATEGORY_META.get(name, {})


def seed() -> None:
    db = SessionLocal()
    repo = CategoryRepository(db)
    created = 0
    updated = 0

    def ensure_category(name: str, category_type: str, parent_id: int | None = None) -> Category:
        nonlocal created, updated
        meta = _meta_for(name, category_type, parent_id)
        existing = repo.find_system_by_name_and_type(name, category_type, parent_id)
        if existing:
            changed = False
            if meta.get("icon") and existing.icon != meta["icon"]:
                existing.icon = meta["icon"]
                changed = True
            if meta.get("color") and existing.color != meta["color"]:
                existing.color = meta["color"]
                changed = True
            if changed:
                updated += 1
            return existing
        category = Category(
            uid=new_uid(),
            user_id=None,
            parent_id=parent_id,
            name=name,
            type=category_type,
            icon=meta.get("icon"),
            color=meta.get("color"),
        )
        repo.create(category)
        created += 1
        return category

    for parent_name, children in EXPENSE_CATEGORIES.items():
        parent = ensure_category(parent_name, CategoryType.EXPENSE.value)
        for child_name in children:
            ensure_category(child_name, CategoryType.EXPENSE.value, parent.id)

    for parent_name, children in INCOME_CATEGORIES.items():
        parent = ensure_category(parent_name, CategoryType.INCOME.value)
        for child_name in children:
            ensure_category(child_name, CategoryType.INCOME.value, parent.id)

    db.commit()
    db.close()
    print(f"✅ Сидер категорий завершён. Создано: {created}, обновлено icon/color: {updated}")


if __name__ == "__main__":
    seed()
