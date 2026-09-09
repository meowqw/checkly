"""Сервис категорий (плоский список)."""
from sqlalchemy.orm import Session

from app.core.category_taxonomy import normalize_expense_category
from app.core.enums import CategoryType
from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.core.uuid_utils import new_uid
from app.database.models import Category
from app.dto.accounts import SuccessResponseDTO
from app.dto.categories import (
    CategoriesListResponseDTO,
    CategoryDTO,
    CategoryResponseDTO,
    CreateCategoryRequestDTO,
    UpdateCategoryRequestDTO,
)
from app.repositories.category_repository import CategoryRepository


class CategoryService:
    def __init__(self, db: Session):
        self._categories = CategoryRepository(db)
        self._db = db

    def list_categories(self, user_id: int) -> CategoriesListResponseDTO:
        rows = self._categories.list_for_user(user_id)
        return CategoriesListResponseDTO(
            categories=[self._to_dto(c, usage_count=count) for c, count in rows]
        )

    def create_category(self, user_id: int, dto: CreateCategoryRequestDTO) -> CategoryResponseDTO:
        name = dto.name.strip()
        self._ensure_unique_name(user_id, name, dto.type.value)

        category = Category(
            uid=new_uid(),
            user_id=user_id,
            name=name,
            type=dto.type.value,
            icon=dto.icon,
            color=dto.color,
        )
        self._categories.create(category)
        self._db.commit()
        self._db.refresh(category)
        return CategoryResponseDTO(category=self._to_dto(category, usage_count=0))

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
                exclude_id=category.id,
            )
            category.name = name
        if dto.icon is not None:
            category.icon = dto.icon
        if dto.color is not None:
            category.color = dto.color
        self._db.commit()
        self._db.refresh(category)
        return CategoryResponseDTO(category=self._to_dto(category, usage_count=0))

    def delete_category(self, user_id: int, category_uid: str) -> SuccessResponseDTO:
        category = self._get_user_owned_category(category_uid, user_id)
        self._categories.delete(category)
        self._db.commit()
        return SuccessResponseDTO()

    def find_system_for_receipt(
        self,
        category_name: str,
        category_type: str = CategoryType.EXPENSE.value,
    ) -> Category | None:
        """Lookup системной категории по имени — без создания."""
        safe_name = normalize_expense_category(category_name)
        category = self._categories.find_system_by_name_and_type(safe_name, category_type)
        if not category:
            category = self._categories.find_system_by_name_and_type("Прочее", category_type)
        return category

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
        *,
        exclude_id: int | None = None,
    ) -> None:
        if not name:
            raise AppError("Название категории не может быть пустым")
        existing = self._categories.find_visible_by_name(
            user_id,
            name,
            category_type,
            exclude_id=exclude_id,
        )
        if existing:
            raise ConflictError("Категория с таким названием уже есть")

    def _to_dto(self, category: Category, *, usage_count: int = 0) -> CategoryDTO:
        return CategoryDTO(
            id=category.uid,
            name=category.name,
            type=category.type,
            icon=category.icon,
            color=category.color,
            is_custom=category.user_id is not None,
            usage_count=usage_count,
        )
