"""Роутер тегов."""
from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.dto.accounts import SuccessResponseDTO
from app.dto.tags import CreateTagRequestDTO, TagResponseDTO, TagsListResponseDTO
from app.openapi import COMMON_ERROR_RESPONSES
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])

_AUTH_ERRORS = {401: COMMON_ERROR_RESPONSES[401]}


@router.get(
    "",
    response_model=TagsListResponseDTO,
    summary="Список тегов",
    description=(
        "Системные и пользовательские теги. Независимы от категорий: "
        "один тег может использоваться с любой категорией."
    ),
    responses=_AUTH_ERRORS,
)
def list_tags(db: DbSession, user: CurrentUser) -> TagsListResponseDTO:
    return TagService(db).list_tags(user.id)


@router.post(
    "",
    response_model=TagResponseDTO,
    summary="Создать тег",
    description="Пользовательский тег. Имя уникально среди системных и своих.",
    responses={
        **_AUTH_ERRORS,
        400: COMMON_ERROR_RESPONSES[400],
        409: COMMON_ERROR_RESPONSES[409],
    },
)
def create_tag(dto: CreateTagRequestDTO, db: DbSession, user: CurrentUser) -> TagResponseDTO:
    return TagService(db).create_tag(user.id, dto)


@router.delete(
    "/{tag_id}",
    response_model=SuccessResponseDTO,
    summary="Удалить тег",
    description="Только пользовательский тег. Системные удалить нельзя.",
    responses={
        **_AUTH_ERRORS,
        403: COMMON_ERROR_RESPONSES[403],
        404: COMMON_ERROR_RESPONSES[404],
    },
)
def delete_tag(tag_id: str, db: DbSession, user: CurrentUser) -> SuccessResponseDTO:
    return TagService(db).delete_tag(user.id, tag_id)
