"""Сидер системных категорий расходов и доходов."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.category_taxonomy import EXPENSE_TAXONOMY
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


def seed() -> None:
    db = SessionLocal()
    repo = CategoryRepository(db)
    created = 0

    def ensure_category(name: str, category_type: str, parent_id: int | None = None) -> Category:
        nonlocal created
        existing = repo.find_system_by_name_and_type(name, category_type, parent_id)
        if existing:
            return existing
        category = Category(
            uid=new_uid(),
            user_id=None,
            parent_id=parent_id,
            name=name,
            type=category_type,
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
    print(f"✅ Сидер категорий завершён. Создано записей: {created}")


if __name__ == "__main__":
    seed()
