"""Категории: системные read-only, свои — editable."""
import pytest
from sqlalchemy.orm import Session

from app.core.enums import CategoryType
from app.core.exceptions import ForbiddenError
from app.database.models import Category, User
from app.dto.categories import CreateCategoryRequestDTO, UpdateCategoryRequestDTO
from app.services.category_service import CategoryService


def test_create_and_update_custom_category(db: Session, user: User) -> None:
    service = CategoryService(db)
    created = service.create_category(
        user.id,
        CreateCategoryRequestDTO(
            name="Хобби",
            type=CategoryType.EXPENSE,
            icon="palette",
            color="#0d9488",
        ),
    )
    assert created.category.is_custom is True

    updated = service.update_category(
        user.id,
        created.category.id,
        UpdateCategoryRequestDTO(name="Хобби 2"),
    )
    assert updated.category.name == "Хобби 2"

    service.delete_category(user.id, created.category.id)
    listing = service.list_categories(user.id)
    assert all(c.id != created.category.id for c in listing.categories)


def test_cannot_update_system_category(
    db: Session, user: User, system_categories: dict[str, Category]
) -> None:
    with pytest.raises(ForbiddenError):
        CategoryService(db).update_category(
            user.id,
            system_categories["products"].uid,
            UpdateCategoryRequestDTO(name="Hack"),
        )


def test_cannot_delete_system_category(
    db: Session, user: User, system_categories: dict[str, Category]
) -> None:
    with pytest.raises(ForbiddenError):
        CategoryService(db).delete_category(user.id, system_categories["products"].uid)


def test_find_system_for_receipt(
    db: Session, system_categories: dict[str, Category]
) -> None:
    service = CategoryService(db)
    found = service.find_system_for_receipt("Продукты", "Молочные")
    assert found is not None
    assert found.id == system_categories["dairy"].id

    parent_only = service.find_system_for_receipt("Продукты", "Несуществующая")
    assert parent_only is not None
    assert parent_only.id == system_categories["products"].id
