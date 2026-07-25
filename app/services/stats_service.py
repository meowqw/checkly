"""Агрегация статистики по транзакциям."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.category_display import category_display_name
from app.core.enums import TransactionType
from app.database.models import Category
from app.dto.stats import CategoryStatDTO, StatsResponseDTO
from app.dto.transactions import TransactionFilterDTO
from app.repositories.transaction_repository import TransactionRepository
from app.services.transaction_mapper import map_transaction_to_list_item
from app.services.transaction_queries import resolve_transaction_filters

RECENT_EXPENSES_LIMIT = 8
FALLBACK_CATEGORY = "Прочее"


class StatsService:
    def __init__(self, db: Session):
        self._transactions = TransactionRepository(db)

    def get_stats(self, filters: TransactionFilterDTO) -> StatsResponseDTO:
        resolved = resolve_transaction_filters(self._transactions, filters)

        sums = self._transactions.sum_amounts_by_type(
            resolved.user_id,
            from_date=resolved.from_date,
            to_date=resolved.to_date,
            account_id=resolved.account_id,
        )
        expense = sums.get(TransactionType.EXPENSE.value, 0)
        income = sums.get(TransactionType.INCOME.value, 0)

        categories = self._build_category_stats(
            resolved.user_id,
            from_date=resolved.from_date,
            to_date=resolved.to_date,
            account_id=resolved.account_id,
        )

        recent_rows = self._transactions.list_recent_expenses(
            resolved.user_id,
            from_date=resolved.from_date,
            to_date=resolved.to_date,
            account_id=resolved.account_id,
            limit=RECENT_EXPENSES_LIMIT,
        )
        recent = [map_transaction_to_list_item(t, compact=True) for t in recent_rows]

        return StatsResponseDTO(
            expense=expense,
            income=income,
            categories=categories,
            recent_expenses=recent,
        )

    def _build_category_stats(
        self,
        user_id: int,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        account_id: int | None,
    ) -> list[CategoryStatDTO]:
        rows = self._transactions.aggregate_expense_category_amounts(
            user_id,
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
        )
        if not rows:
            return []

        category_ids = [cid for cid, _ in rows if cid is not None]
        categories_by_id = self._transactions.get_categories_with_parents(category_ids)

        # Схлопываем по display-name (как раньше: ключ — имя, не id)
        totals: dict[str, tuple[int, str | None, str | None]] = {}
        for category_id, amount in rows:
            name, uid, color = self._category_meta(category_id, categories_by_id)
            prev_amount, prev_uid, prev_color = totals.get(name, (0, None, None))
            totals[name] = (
                prev_amount + amount,
                prev_uid or uid,
                prev_color or color,
            )

        total_amount = sum(amount for amount, _, _ in totals.values()) or 1
        stats = [
            CategoryStatDTO(
                category_id=uid,
                name=name,
                amount=amount,
                percent=round(amount / total_amount * 100),
                color=color,
            )
            for name, (amount, uid, color) in totals.items()
        ]
        stats.sort(key=lambda row: row.amount, reverse=True)
        return stats

    @staticmethod
    def _category_meta(
        category_id: int | None, categories_by_id: dict[int, Category]
    ) -> tuple[str, str | None, str | None]:
        if category_id is None:
            return FALLBACK_CATEGORY, None, None
        cat = categories_by_id.get(category_id)
        if not cat:
            return FALLBACK_CATEGORY, None, None
        color = cat.color or (cat.parent.color if cat.parent else None)
        return category_display_name(cat) or FALLBACK_CATEGORY, cat.uid, color
