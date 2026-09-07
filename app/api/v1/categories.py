"""Роутер категорий."""
from fastapi import APIRouter

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
    description="Плоский список системных и пользовательских категорий (без иерархии).",
    responses=_AUTH_ERRORS,
)
def list_categories(db: DbSession, user: CurrentUser) -> CategoriesListResponseDTO:
    return CategoryService(db).list_categories(user.id)


@router.post(
    "",
    response_model=CategoryResponseDTO,
    summary="Создать категорию",
    description="Создаёт пользовательскую категорию. Имя уникально среди системных и своих того же типа.",
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
    description="Название, иконка, цвет. Только пользовательские категории.",
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
    description="Удаляет пользовательскую категорию. Системные удалить нельзя.",
    responses={**_AUTH_ERRORS, 404: COMMON_ERROR_RESPONSES[404], 409: COMMON_ERROR_RESPONSES[409]},
)
def delete_category(
    category_id: str, db: DbSession, user: CurrentUser
) -> SuccessResponseDTO:
    return CategoryService(db).delete_category(user.id, category_id)
