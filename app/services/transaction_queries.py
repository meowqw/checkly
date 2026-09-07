"""Общая загрузка транзакций по фильтрам."""
from dataclasses import dataclass
from datetime import datetime

from app.core.dates import normalize_range_end, normalize_range_start
from app.core.exceptions import NotFoundError
from app.database.models import Transaction
from app.dto.transactions import TransactionFilterDTO
from app.repositories.category_repository import CategoryRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.transaction_repository import TransactionRepository


@dataclass(frozen=True)
class ResolvedTransactionFilters:
    user_id: int
    from_date: datetime | None
    to_date: datetime | None
    transaction_type: str | None
    account_id: int | None
    category_ids: list[int] | None = None
    tag_ids: list[int] | None = None


def resolve_category_filter(
    categories: CategoryRepository, user_id: int, category_uid: str | None
) -> list[int] | None:
    """None = без фильтра; иначе exact match по одной категории."""
    if not category_uid:
        return None
    category = categories.get_by_uid_for_user(category_uid, user_id)
    if not category:
        raise NotFoundError("Категория не найдена")
    return [category.id]


def resolve_tag_filter(
    tags: TagRepository, user_id: int, tag_uid: str | None
) -> list[int] | None:
    if not tag_uid:
        return None
    tag = tags.get_by_uid_for_user(tag_uid, user_id)
    if not tag:
        raise NotFoundError("Тег не найден")
    return [tag.id]


def resolve_transaction_filters(
    repo: TransactionRepository,
    filters: TransactionFilterDTO,
    *,
    categories: CategoryRepository,
    tags: TagRepository,
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
        category_ids=resolve_category_filter(
            categories, filters.user_id, filters.category_uid
        ),
        tag_ids=resolve_tag_filter(tags, filters.user_id, filters.tag_uid),
    )


def list_transactions_for_filters(
    repo: TransactionRepository,
    filters: TransactionFilterDTO,
    *,
    categories: CategoryRepository,
    tags: TagRepository,
) -> list[Transaction]:
    resolved = resolve_transaction_filters(
        repo, filters, categories=categories, tags=tags
    )
    return repo.list_for_user(
        user_id=resolved.user_id,
        from_date=resolved.from_date,
        to_date=resolved.to_date,
        transaction_type=resolved.transaction_type,
        account_id=resolved.account_id,
        category_ids=resolved.category_ids,
        tag_ids=resolved.tag_ids,
        limit=filters.limit,
        offset=filters.offset,
    )
