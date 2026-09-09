"""Сервис тегов (независимы от категорий)."""
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.core.uuid_utils import new_uid
from app.database.models import Tag
from app.dto.accounts import SuccessResponseDTO
from app.dto.tags import CreateTagRequestDTO, TagDTO, TagResponseDTO, TagsListResponseDTO
from app.repositories.tag_repository import TagRepository


class TagService:
    def __init__(self, db: Session):
        self._tags = TagRepository(db)
        self._db = db

    def list_tags(self, user_id: int) -> TagsListResponseDTO:
        rows = self._tags.list_for_user(user_id)
        return TagsListResponseDTO(
            tags=[self._to_dto(tag, usage_count=count) for tag, count in rows]
        )

    def create_tag(self, user_id: int, dto: CreateTagRequestDTO) -> TagResponseDTO:
        name = dto.name.strip()
        self._ensure_unique_name(user_id, name)
        tag = Tag(
            uid=new_uid(),
            user_id=user_id,
            name=name,
            icon=dto.icon,
            color=dto.color,
        )
        self._tags.create(tag)
        self._db.commit()
        self._db.refresh(tag)
        return TagResponseDTO(tag=self._to_dto(tag, usage_count=0))

    def delete_tag(self, user_id: int, tag_uid: str) -> SuccessResponseDTO:
        tag = self._tags.get_user_tag(tag_uid, user_id)
        if not tag:
            raise ForbiddenError("Нельзя удалять системный или чужой тег")
        self._tags.delete(tag)
        self._db.commit()
        return SuccessResponseDTO()

    def resolve_system_tags(self, names: list[str]) -> list[Tag]:
        """Найти системные теги по каноническим именам (порядок сохраняем)."""
        if not names:
            return []
        found = {t.name: t for t in self._tags.find_system_by_names(names)}
        return [found[n] for n in names if n in found]

    def resolve_tags_for_user(self, user_id: int, tag_uids: list[str]) -> list[Tag]:
        tags: list[Tag] = []
        for uid in tag_uids:
            tag = self._tags.get_by_uid_for_user(uid, user_id)
            if not tag:
                raise NotFoundError("Тег не найден")
            tags.append(tag)
        return tags

    def _ensure_unique_name(
        self, user_id: int, name: str, *, exclude_id: int | None = None
    ) -> None:
        if not name:
            raise AppError("Название тега не может быть пустым")
        existing = self._tags.find_visible_by_name(user_id, name, exclude_id=exclude_id)
        if existing:
            raise ConflictError("Тег с таким названием уже есть")

    def _to_dto(self, tag: Tag, *, usage_count: int = 0) -> TagDTO:
        return TagDTO(
            id=tag.uid,
            name=tag.name,
            icon=tag.icon,
            color=tag.color,
            is_custom=tag.user_id is not None,
            usage_count=usage_count,
        )
