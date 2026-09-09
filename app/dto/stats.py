"""DTO для статистики."""
from pydantic import BaseModel, Field

from app.dto.transactions import TransactionListItemDTO


class CategoryStatDTO(BaseModel):
    category_id: str | None = Field(default=None, description="UUID категории (если известна)")
    name: str = Field(description="Имя категории")
    amount: int = Field(description="Сумма в копейках")
    percent: int = Field(description="Доля от суммы разбивки по категориям, %")
    color: str | None = Field(default=None, description="Цвет категории #RRGGBB")


class TagStatDTO(BaseModel):
    tag_id: str | None = Field(
        default=None,
        description="UUID тега; null = позиции без тегов («Без тега»)",
    )
    name: str = Field(description="Имя тега")
    amount: int = Field(description="Сумма в копейках")
    percent: int = Field(
        description="Доля от суммы разбивки по тегам, % (позиция с несколькими тегами учитывается в каждом)"
    )
    color: str | None = Field(default=None, description="Цвет тега #RRGGBB")


class StatsResponseDTO(BaseModel):
    expense: int = Field(description="Сумма расходов за период в копейках")
    income: int = Field(description="Сумма доходов за период в копейках")
    categories: list[CategoryStatDTO] = Field(description="Разбивка расходов по категориям")
    tags: list[TagStatDTO] = Field(
        default_factory=list,
        description="Разбивка расходов по тегам (позиции; multi-tag — полная сумма в каждом теге)",
    )
    recent_expenses: list[TransactionListItemDTO] = Field(
        description="Последние расходы за период (до 8 шт.)"
    )
