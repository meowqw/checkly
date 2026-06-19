"""DTO для категорий."""
from pydantic import BaseModel, Field

from app.core.enums import CategoryType


class CategoryDTO(BaseModel):
    id: str = Field(description="UUID категории")
    name: str = Field(description="Название")
    type: str = Field(description="Тип: expense (расход) или income (доход)")
    parent_id: str | None = Field(default=None, description="UUID родительской категории")
    icon: str | None = Field(default=None, description="Иконка (эмодзи или код)")
    color: str | None = Field(default=None, description="Цвет в формате #RRGGBB")
    is_custom: bool = Field(default=False, description="Создана пользователем")
    children: list["CategoryDTO"] | None = Field(default=None, description="Дочерние категории")


CategoryDTO.model_rebuild()


class CategoriesListResponseDTO(BaseModel):
    categories: list[CategoryDTO] = Field(description="Список категорий")


class CreateCategoryRequestDTO(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Название")
    type: CategoryType = Field(description="Тип: expense или income")
    parent_id: str | None = Field(default=None, description="UUID родителя (для подкатегории)")
    icon: str | None = Field(default=None, description="Иконка")
    color: str | None = Field(default=None, description="Цвет #RRGGBB")


class UpdateCategoryRequestDTO(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255, description="Новое название")
    icon: str | None = Field(default=None, description="Новая иконка")
    color: str | None = Field(default=None, description="Новый цвет")


class CategoryResponseDTO(BaseModel):
    category: CategoryDTO = Field(description="Категория")
