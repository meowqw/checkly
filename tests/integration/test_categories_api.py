"""Категории и теги через API."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import CategoryType
from app.core.exceptions import ForbiddenError
from app.core.uuid_utils import new_uid
from app.database.models import Category, User
from app.services.category_service import CategoryService
import pytest


def test_categories_api_flat_list(
    client: TestClient,
    system_categories: dict,
    auth_headers: dict[str, str],
) -> None:
    flat = client.get("/v1/categories", headers=auth_headers)
    assert flat.status_code == 200
    names = {c["name"] for c in flat.json()["categories"]}
    assert "Продукты" in names
    assert "Молочные" not in names  # тег, не категория
    for cat in flat.json()["categories"]:
        assert "parent_id" not in cat or cat.get("parent_id") is None
        assert cat.get("children") in (None, [],)


def test_tags_api_list(
    client: TestClient,
    system_categories: dict,
    auth_headers: dict[str, str],
) -> None:
    res = client.get("/v1/tags", headers=auth_headers)
    assert res.status_code == 200
    names = {t["name"] for t in res.json()["tags"]}
    assert "Молочные" in names
    assert "Снэки" in names


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


def test_tags_api_custom_crud(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        "/v1/tags",
        headers=auth_headers,
        json={"name": "Свой тег"},
    )
    assert created.status_code == 200
    tag_id = created.json()["tag"]["id"]
    assert created.json()["tag"]["is_custom"] is True
    assert client.delete(f"/v1/tags/{tag_id}", headers=auth_headers).status_code == 200


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
