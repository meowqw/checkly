"""Роутер категорий."""
from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.dto.accounts import SuccessResponseDTO
from app.dto.categories import (
    CategoriesListResponseDTO,
    CategoryResponseDTO,
    CreateCategoryRequestDTO,
    UpdateCategoryRequestDTO,
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoriesListResponseDTO)
def list_categories(
    db: DbSession,
    user: CurrentUser,
    include: str | None = Query(default=None),
) -> CategoriesListResponseDTO:
    include_children = include == "children"
    return CategoryService(db).list_categories(user.id, include_children=include_children)


@router.post("", response_model=CategoryResponseDTO)
def create_category(
    dto: CreateCategoryRequestDTO, db: DbSession, user: CurrentUser
) -> CategoryResponseDTO:
    return CategoryService(db).create_category(user.id, dto)


@router.patch("/{category_id}", response_model=CategoryResponseDTO)
def update_category(
    category_id: str,
    dto: UpdateCategoryRequestDTO,
    db: DbSession,
    user: CurrentUser,
) -> CategoryResponseDTO:
    return CategoryService(db).update_category(user.id, category_id, dto)


@router.delete("/{category_id}", response_model=SuccessResponseDTO)
def delete_category(
    category_id: str, db: DbSession, user: CurrentUser
) -> SuccessResponseDTO:
    return CategoryService(db).delete_category(user.id, category_id)
