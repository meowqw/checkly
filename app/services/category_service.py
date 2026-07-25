"""Сервис категорий."""
from sqlalchemy.orm import Session

from app.core.category_taxonomy import EXPENSE_TAXONOMY, normalize_expense_category
from app.core.enums import CategoryType
from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
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
                    is_custom=c.user_id is not None,
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
            if parent.type != dto.type.value:
                raise ConflictError("Тип категории должен совпадать с родительской")
            parent_id = parent.id

        name = dto.name.strip()
        self._ensure_unique_name(user_id, name, dto.type.value, parent_id)

        category = Category(
            uid=new_uid(),
            user_id=user_id,
            parent_id=parent_id,
            name=name,
            type=dto.type.value,
            icon=dto.icon,
            color=dto.color,
        )
        self._categories.create(category)
        self._db.commit()
        self._db.refresh(category)
        return CategoryResponseDTO(category=self._to_dto(category, dto.parent_id))

    def update_category(
        self, user_id: int, category_uid: str, dto: UpdateCategoryRequestDTO
    ) -> CategoryResponseDTO:
        category = self._get_user_owned_category(category_uid, user_id)
        if dto.name is not None:
            name = dto.name.strip()
            self._ensure_unique_name(
                user_id,
                name,
                category.type,
                category.parent_id,
                exclude_id=category.id,
            )
            category.name = name
        if dto.icon is not None:
            category.icon = dto.icon
        if dto.color is not None:
            category.color = dto.color
        self._db.commit()
        self._db.refresh(category)
        parent_uid = None
        if category.parent_id:
            parent = self._db.get(Category, category.parent_id)
            parent_uid = parent.uid if parent else None
        return CategoryResponseDTO(category=self._to_dto(category, parent_uid))

    def delete_category(self, user_id: int, category_uid: str) -> SuccessResponseDTO:
        category = self._get_user_owned_category(category_uid, user_id)
        self._categories.delete(category)
        self._db.commit()
        return SuccessResponseDTO()

    def find_system_for_receipt(
        self,
        category_name: str,
        subcategory_name: str | None,
        category_type: str = CategoryType.EXPENSE.value,
    ) -> Category | None:
        """Только lookup по системным категориям — без создания новых."""
        safe_name = normalize_expense_category(category_name)
        subcategory_name = subcategory_name if safe_name in EXPENSE_TAXONOMY else None

        parent = self._categories.find_system_by_name_and_type(safe_name, category_type)
        if not parent:
            parent = self._categories.find_system_by_name_and_type("Прочее", category_type)
        if not parent:
            return None

        if subcategory_name:
            child = self._categories.find_system_by_name_and_type(
                subcategory_name, category_type, parent_id=parent.id
            )
            if child:
                return child

        return parent

    def _get_user_owned_category(self, category_uid: str, user_id: int) -> Category:
        category = self._categories.get_user_category(category_uid, user_id)
        if not category:
            raise ForbiddenError("Нельзя изменять системную или чужую категорию")
        return category

    def _ensure_unique_name(
        self,
        user_id: int,
        name: str,
        category_type: str,
        parent_id: int | None,
        *,
        exclude_id: int | None = None,
    ) -> None:
        if not name:
            raise AppError("Название категории не может быть пустым")
        existing = self._categories.find_visible_by_name(
            user_id,
            name,
            category_type,
            parent_id,
            exclude_id=exclude_id,
        )
        if existing:
            raise ConflictError("Категория с таким названием уже есть")

    def _to_tree_dto(self, category: Category, all_categories: list[Category]) -> CategoryDTO:
        children = [c for c in all_categories if c.parent_id == category.id]
        return CategoryDTO(
            id=category.uid,
            name=category.name,
            type=category.type,
            icon=category.icon,
            color=category.color,
            is_custom=category.user_id is not None,
            children=[self._to_tree_dto(child, all_categories) for child in children] or None,
        )

    def _to_dto(self, category: Category, parent_uid: str | None = None) -> CategoryDTO:
        return CategoryDTO(
            id=category.uid,
            name=category.name,
            type=category.type,
            parent_id=parent_uid,
            icon=category.icon,
            color=category.color,
            is_custom=category.user_id is not None,
        )

    def _parent_uid(self, category: Category, all_categories: list[Category]) -> str | None:
        if not category.parent_id:
            return None
        parent = next((c for c in all_categories if c.id == category.parent_id), None)
        return parent.uid if parent else None
