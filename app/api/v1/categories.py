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
from app.openapi import COMMON_ERROR_RESPONSES
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])

_AUTH_ERRORS = {401: COMMON_ERROR_RESPONSES[401]}


@router.get(
    "",
    response_model=CategoriesListResponseDTO,
    summary="Список категорий",
    description=(
        "Возвращает категории пользователя (системные и пользовательские). "
        "Передайте `include=children` для вложенного дерева подкатегорий."
    ),
    responses=_AUTH_ERRORS,
)
def list_categories(
    db: DbSession,
    user: CurrentUser,
    include: str | None = Query(
        default=None,
        description='Вложенные подкатегории: передайте "children" или оставьте пустым',
    ),
) -> CategoriesListResponseDTO:
    include_children = include == "children"
    return CategoryService(db).list_categories(user.id, include_children=include_children)


@router.post(
    "",
    response_model=CategoryResponseDTO,
    summary="Создать категорию",
    description=(
        "Создаёт пользовательскую категорию или подкатегорию. "
        "Имя должно быть уникально среди системных и своих на том же уровне."
    ),
    responses={
        **_AUTH_ERRORS,
        400: COMMON_ERROR_RESPONSES[400],
        409: COMMON_ERROR_RESPONSES[409],
    },
)
def create_category(
    dto: CreateCategoryRequestDTO, db: DbSession, user: CurrentUser
) -> CategoryResponseDTO:
    return CategoryService(db).create_category(user.id, dto)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponseDTO,
    summary="Обновить категорию",
    description=(
        "Можно менять название, иконку и цвет. Только пользовательские категории. "
        "Новое имя не должно совпадать с уже существующим на том же уровне."
    ),
    responses={
        **_AUTH_ERRORS,
        404: COMMON_ERROR_RESPONSES[404],
        409: COMMON_ERROR_RESPONSES[409],
    },
)
def update_category(
    category_id: str,
    dto: UpdateCategoryRequestDTO,
    db: DbSession,
    user: CurrentUser,
) -> CategoryResponseDTO:
    return CategoryService(db).update_category(user.id, category_id, dto)


@router.delete(
    "/{category_id}",
    response_model=SuccessResponseDTO,
    summary="Удалить категорию",
    description="Удаляет пользовательскую категорию. Системные категории удалить нельзя.",
    responses={**_AUTH_ERRORS, 404: COMMON_ERROR_RESPONSES[404], 409: COMMON_ERROR_RESPONSES[409]},
)
def delete_category(
    category_id: str, db: DbSession, user: CurrentUser
) -> SuccessResponseDTO:
    return CategoryService(db).delete_category(user.id, category_id)
