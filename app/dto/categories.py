"""DTO для категорий."""
from pydantic import BaseModel, Field

from app.core.enums import CategoryType


class CategoryDTO(BaseModel):
    id: str
    name: str
    type: str
    parent_id: str | None = None
    icon: str | None = None
    color: str | None = None
    children: list["CategoryDTO"] | None = None


CategoryDTO.model_rebuild()


class CategoriesListResponseDTO(BaseModel):
    categories: list[CategoryDTO]


class CreateCategoryRequestDTO(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: CategoryType
    parent_id: str | None = None
    icon: str | None = None
    color: str | None = None


class UpdateCategoryRequestDTO(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    icon: str | None = None
    color: str | None = None


class CategoryResponseDTO(BaseModel):
    category: CategoryDTO
