"""Общая загрузка транзакций по фильтрам."""
from app.core.dates import normalize_range_end, normalize_range_start
from app.core.exceptions import NotFoundError
from app.database.models import Transaction
from app.dto.transactions import TransactionFilterDTO
from app.repositories.transaction_repository import TransactionRepository


def list_transactions_for_filters(
    repo: TransactionRepository, filters: TransactionFilterDTO
) -> list[Transaction]:
    account_id = None
    if filters.account_uid:
        account_id = repo.get_account_id_by_uid(filters.account_uid, filters.user_id)
        if not account_id:
            raise NotFoundError("Счёт не найден")

    return repo.list_for_user(
        user_id=filters.user_id,
        from_date=normalize_range_start(filters.from_date, filters.timezone),
        to_date=normalize_range_end(filters.to_date, filters.timezone),
        transaction_type=filters.type.value if filters.type else None,
        account_id=account_id,
    )
