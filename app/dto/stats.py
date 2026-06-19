"""DTO для статистики."""
from pydantic import BaseModel, Field

from app.dto.transactions import TransactionListItemDTO


class CategoryStatDTO(BaseModel):
    category_id: str | None = Field(default=None, description="UUID категории (если известна)")
    name: str = Field(description="Отображаемое имя: «Родитель › Подкатегория» или корень")
    amount: int = Field(description="Сумма в копейках")
    percent: int = Field(description="Доля от общих расходов за период, %")
    color: str | None = Field(default=None, description="Цвет категории #RRGGBB")


class StatsResponseDTO(BaseModel):
    expense: int = Field(description="Сумма расходов за период в копейках")
    income: int = Field(description="Сумма доходов за период в копейках")
    categories: list[CategoryStatDTO] = Field(description="Разбивка расходов по категориям")
    recent_expenses: list[TransactionListItemDTO] = Field(
        description="Последние расходы за период (до 8 шт.)"
    )
