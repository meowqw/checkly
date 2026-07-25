"""Категории через API: дерево, parent conflict, чужие."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import CategoryType
from app.core.exceptions import ConflictError, ForbiddenError
from app.core.uuid_utils import new_uid
from app.database.models import Category, User
from app.dto.categories import CreateCategoryRequestDTO
from app.services.category_service import CategoryService
import pytest


def test_categories_api_list_tree(
    client: TestClient,
    system_categories: dict[str, Category],
    auth_headers: dict[str, str],
) -> None:
    flat = client.get("/v1/categories", headers=auth_headers)
    assert flat.status_code == 200
    names = {c["name"] for c in flat.json()["categories"]}
    assert "Продукты" in names
    assert "Молочные" in names

    tree = client.get("/v1/categories", params={"include": "children"}, headers=auth_headers)
    assert tree.status_code == 200
    roots = tree.json()["categories"]
    products = next(c for c in roots if c["name"] == "Продукты")
    child_names = {c["name"] for c in (products.get("children") or [])}
    assert "Молочные" in child_names


def test_categories_api_custom_crud(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post(
        "/v1/categories",
        headers=auth_headers,
        json={"name": "Своя", "type": "expense", "color": "#111111"},
    )
    assert created.status_code == 200
    cat_id = created.json()["category"]["id"]
    assert created.json()["category"]["is_custom"] is True

    patched = client.patch(
        f"/v1/categories/{cat_id}",
        headers=auth_headers,
        json={"name": "Своя 2"},
    )
    assert patched.json()["category"]["name"] == "Своя 2"

    assert client.delete(f"/v1/categories/{cat_id}", headers=auth_headers).status_code == 200


def test_parent_type_mismatch_conflict(
    db: Session, user: User, system_categories: dict[str, Category]
) -> None:
    with pytest.raises(ConflictError):
        CategoryService(db).create_category(
            user.id,
            CreateCategoryRequestDTO(
                name="Нельзя",
                type=CategoryType.INCOME,
                parent_id=system_categories["products"].uid,
            ),
        )


def test_cannot_modify_other_user_category(
    db: Session, user: User, other_user: User
) -> None:
    alien = Category(
        uid=new_uid(),
        user_id=other_user.id,
        name="Чужая",
        type=CategoryType.EXPENSE.value,
    )
    db.add(alien)
    db.commit()
    with pytest.raises(ForbiddenError):
        CategoryService(db).delete_category(user.id, alien.uid)
