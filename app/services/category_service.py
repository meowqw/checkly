"""Сервис категорий."""
from sqlalchemy.orm import Session

from app.core.enums import CategoryType
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.uuid_utils import new_uid
from app.database.models import Category
from app.dto.categories import (
    CategoriesListResponseDTO,
    CategoryDTO,
    CategoryResponseDTO,
    CreateCategoryRequestDTO,
    UpdateCategoryRequestDTO,
)
from app.dto.accounts import SuccessResponseDTO
from app.repositories.category_repository import CategoryRepository


class CategoryService:
    def __init__(self, db: Session):
        self._categories = CategoryRepository(db)
        self._db = db

    def list_categories(self, user_id: int, include_children: bool = False) -> CategoriesListResponseDTO:
        categories = self._categories.list_for_user(user_id)
        if include_children:
            roots = [c for c in categories if c.parent_id is None]
            return CategoriesListResponseDTO(
                categories=[self._to_tree_dto(root, categories) for root in roots]
            )
        return CategoriesListResponseDTO(
            categories=[
                CategoryDTO(
                    id=c.uid,
                    name=c.name,
                    type=c.type,
                    parent_id=self._parent_uid(c, categories),
                    icon=c.icon,
                    color=c.color,
                )
                for c in categories
            ]
        )

    def create_category(self, user_id: int, dto: CreateCategoryRequestDTO) -> CategoryResponseDTO:
        parent_id = None
        if dto.parent_id:
            parent = self._categories.get_by_uid_for_user(dto.parent_id, user_id)
            if not parent:
                raise NotFoundError("Родительская категория не найдена")
            parent_id = parent.id

        category = Category(
            uid=new_uid(),
            user_id=user_id,
            parent_id=parent_id,
            name=dto.name,
            type=dto.type.value,
            icon=dto.icon,
            color=dto.color,
        )
        self._categories.create(category)
        self._db.commit()
        self._db.refresh(category)
        return CategoryResponseDTO(
            category=CategoryDTO(
                id=category.uid,
                name=category.name,
                type=category.type,
                parent_id=dto.parent_id,
            )
        )

    def update_category(
        self, user_id: int, category_uid: str, dto: UpdateCategoryRequestDTO
    ) -> CategoryResponseDTO:
        category = self._get_user_owned_category(category_uid, user_id)
        if dto.name is not None:
            category.name = dto.name
        if dto.icon is not None:
            category.icon = dto.icon
        if dto.color is not None:
            category.color = dto.color
        self._db.commit()
        self._db.refresh(category)
        return CategoryResponseDTO(
            category=CategoryDTO(id=category.uid, name=category.name, type=category.type)
        )

    def delete_category(self, user_id: int, category_uid: str) -> SuccessResponseDTO:
        category = self._get_user_owned_category(category_uid, user_id)
        self._categories.delete(category)
        self._db.commit()
        return SuccessResponseDTO()

    def find_or_create_from_ai(
        self,
        category_name: str,
        subcategory_name: str | None,
        category_type: str = CategoryType.EXPENSE.value,
    ) -> Category:
        parent = self._categories.find_system_by_name_and_type(category_name, category_type)
        if not parent:
            parent = Category(
                uid=new_uid(),
                user_id=None,
                name=category_name,
                type=category_type,
            )
            self._categories.create(parent)

        if subcategory_name:
            child = self._categories.find_system_by_name_and_type(
                subcategory_name, category_type, parent_id=parent.id
            )
            if not child:
                child = Category(
                    uid=new_uid(),
                    user_id=None,
                    parent_id=parent.id,
                    name=subcategory_name,
                    type=category_type,
                )
                self._categories.create(child)
            return child

        return parent

    def _get_user_owned_category(self, category_uid: str, user_id: int) -> Category:
        category = self._categories.get_user_category(category_uid, user_id)
        if not category:
            raise ForbiddenError("Нельзя изменять системную или чужую категорию")
        return category

    def _to_tree_dto(self, category: Category, all_categories: list[Category]) -> CategoryDTO:
        children = [c for c in all_categories if c.parent_id == category.id]
        return CategoryDTO(
            id=category.uid,
            name=category.name,
            type=category.type,
            icon=category.icon,
            color=category.color,
            children=[self._to_tree_dto(child, all_categories) for child in children] or None,
        )

    def _parent_uid(self, category: Category, all_categories: list[Category]) -> str | None:
        if not category.parent_id:
            return None
        parent = next((c for c in all_categories if c.id == category.parent_id), None)
        return parent.uid if parent else None
