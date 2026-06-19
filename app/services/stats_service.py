"""Агрегация статистики по транзакциям."""
from app.core.category_display import category_display_name
from app.core.enums import TransactionType
from app.database.models import Transaction, TransactionItem
from app.dto.stats import CategoryStatDTO, StatsResponseDTO
from app.dto.transactions import TransactionFilterDTO
from app.repositories.transaction_repository import TransactionRepository
from app.services.transaction_mapper import map_transaction_to_list_item
from app.services.transaction_queries import list_transactions_for_filters

RECENT_EXPENSES_LIMIT = 8
FALLBACK_CATEGORY = "Прочее"


class StatsService:
    def __init__(self, repo: TransactionRepository):
        self._transactions = repo

    def get_stats(self, filters: TransactionFilterDTO) -> StatsResponseDTO:
        rows = list_transactions_for_filters(self._transactions, filters)

        expense = sum(t.amount for t in rows if t.type == TransactionType.EXPENSE.value)
        income = sum(t.amount for t in rows if t.type == TransactionType.INCOME.value)
        categories = self._aggregate_expenses_by_category(rows)

        expense_rows = [t for t in rows if t.type == TransactionType.EXPENSE.value]
        recent = [
            map_transaction_to_list_item(t, compact=True)
            for t in expense_rows[:RECENT_EXPENSES_LIMIT]
        ]

        return StatsResponseDTO(
            expense=expense,
            income=income,
            categories=categories,
            recent_expenses=recent,
        )

    def _aggregate_expenses_by_category(self, rows: list[Transaction]) -> list[CategoryStatDTO]:
        totals: dict[str, tuple[int, str | None, str | None]] = {}

        for tx in rows:
            if tx.type != TransactionType.EXPENSE.value:
                continue

            items = tx.items or []
            if items:
                for item in items:
                    name, uid, color = self._item_category_meta(item)
                    self._add_total(totals, name, item.amount, uid, color)
            else:
                self._add_total(totals, FALLBACK_CATEGORY, tx.amount, None, None)

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

    def _item_category_meta(self, item: TransactionItem) -> tuple[str, str | None, str | None]:
        cat = item.category
        if not cat:
            return FALLBACK_CATEGORY, None, None
        color = cat.color or (cat.parent.color if cat.parent else None)
        return category_display_name(cat) or FALLBACK_CATEGORY, cat.uid, color

    @staticmethod
    def _add_total(
        totals: dict[str, tuple[int, str | None, str | None]],
        name: str,
        amount: int,
        category_uid: str | None,
        color: str | None,
    ) -> None:
        prev_amount, prev_uid, prev_color = totals.get(name, (0, None, None))
        totals[name] = (
            prev_amount + amount,
            prev_uid or category_uid,
            prev_color or color,
        )
