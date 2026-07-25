"""Общая загрузка транзакций по фильтрам."""
from dataclasses import dataclass
from datetime import datetime

from app.core.dates import normalize_range_end, normalize_range_start
from app.core.exceptions import NotFoundError
from app.database.models import Transaction
from app.dto.transactions import TransactionFilterDTO
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository


@dataclass(frozen=True)
class ResolvedTransactionFilters:
    user_id: int
    from_date: datetime | None
    to_date: datetime | None
    transaction_type: str | None
    account_id: int | None
    category_ids: list[int] | None = None


def resolve_category_scope(
    categories: CategoryRepository, user_id: int, category_uid: str | None
) -> list[int] | None:
    """None = без фильтра; корень → id + дети; подкатегория → только она."""
    if not category_uid:
        return None
    category = categories.get_by_uid_for_user(category_uid, user_id)
    if not category:
        raise NotFoundError("Категория не найдена")
    ids = [category.id]
    if category.parent_id is None:
        ids.extend(categories.list_ids_by_parent(category.id))
    return ids


def resolve_transaction_filters(
    repo: TransactionRepository,
    filters: TransactionFilterDTO,
    *,
    categories: CategoryRepository,
) -> ResolvedTransactionFilters:
    account_id = None
    if filters.account_uid:
        account_id = repo.get_account_id_by_uid(filters.account_uid, filters.user_id)
        if not account_id:
            raise NotFoundError("Счёт не найден")

    return ResolvedTransactionFilters(
        user_id=filters.user_id,
        from_date=normalize_range_start(filters.from_date, filters.timezone),
        to_date=normalize_range_end(filters.to_date, filters.timezone),
        transaction_type=filters.type.value if filters.type else None,
        account_id=account_id,
        category_ids=resolve_category_scope(
            categories, filters.user_id, filters.category_uid
        ),
    )


def list_transactions_for_filters(
    repo: TransactionRepository,
    filters: TransactionFilterDTO,
    *,
    categories: CategoryRepository,
) -> list[Transaction]:
    resolved = resolve_transaction_filters(repo, filters, categories=categories)
    return repo.list_for_user(
        user_id=resolved.user_id,
        from_date=resolved.from_date,
        to_date=resolved.to_date,
        transaction_type=resolved.transaction_type,
        account_id=resolved.account_id,
        category_ids=resolved.category_ids,
        limit=filters.limit,
        offset=filters.offset,
    )
