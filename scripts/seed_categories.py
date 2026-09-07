"""Сидер системных категорий и тегов."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.category_taxonomy import (
    EXPENSE_CATEGORIES,
    EXPENSE_CATEGORY_META,
    INCOME_CATEGORIES,
    INCOME_CATEGORY_META,
    SYSTEM_TAGS,
)
from app.core.enums import CategoryType
from app.core.uuid_utils import new_uid
from app.database import SessionLocal
from app.database.models import Category, Tag
from app.repositories.category_repository import CategoryRepository
from app.repositories.tag_repository import TagRepository


def seed() -> None:
    db = SessionLocal()
    cat_repo = CategoryRepository(db)
    tag_repo = TagRepository(db)
    created_cats = 0
    updated_cats = 0
    created_tags = 0

    def ensure_category(name: str, category_type: str, meta: dict[str, str]) -> Category:
        nonlocal created_cats, updated_cats
        existing = cat_repo.find_system_by_name_and_type(name, category_type)
        if existing:
            changed = False
            if meta.get("icon") and existing.icon != meta["icon"]:
                existing.icon = meta["icon"]
                changed = True
            if meta.get("color") and existing.color != meta["color"]:
                existing.color = meta["color"]
                changed = True
            if changed:
                updated_cats += 1
            return existing
        category = Category(
            uid=new_uid(),
            user_id=None,
            name=name,
            type=category_type,
            icon=meta.get("icon"),
            color=meta.get("color"),
        )
        cat_repo.create(category)
        created_cats += 1
        return category

    def ensure_tag(name: str) -> Tag:
        nonlocal created_tags
        existing = tag_repo.find_system_by_name(name)
        if existing:
            return existing
        tag = Tag(uid=new_uid(), user_id=None, name=name)
        tag_repo.create(tag)
        created_tags += 1
        return tag

    for name in EXPENSE_CATEGORIES:
        ensure_category(name, CategoryType.EXPENSE.value, EXPENSE_CATEGORY_META.get(name, {}))

    for name in INCOME_CATEGORIES:
        ensure_category(name, CategoryType.INCOME.value, INCOME_CATEGORY_META.get(name, {}))

    for name in SYSTEM_TAGS:
        ensure_tag(name)

    db.commit()
    db.close()
    print(
        f"✅ Сидер завершён. Категории: +{created_cats}, icon/color: {updated_cats}; "
        f"теги: +{created_tags}"
    )


if __name__ == "__main__":
    seed()
