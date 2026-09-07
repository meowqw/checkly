"""DTO для тегов (независимы от категорий)."""
from pydantic import BaseModel, Field


class TagDTO(BaseModel):
    id: str = Field(description="UUID тега")
    name: str = Field(description="Название")
    icon: str | None = Field(default=None, description="Иконка")
    color: str | None = Field(default=None, description="Цвет #RRGGBB")
    is_custom: bool = Field(default=False, description="Создан пользователем")


class TagsListResponseDTO(BaseModel):
    tags: list[TagDTO] = Field(description="Список тегов (системные + свои)")


class CreateTagRequestDTO(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Название тега")
    icon: str | None = Field(default=None, description="Иконка")
    color: str | None = Field(default=None, description="Цвет #RRGGBB")


class TagResponseDTO(BaseModel):
    tag: TagDTO = Field(description="Тег")


class TagBriefDTO(BaseModel):
    id: str = Field(description="UUID тега")
    name: str = Field(description="Название")
