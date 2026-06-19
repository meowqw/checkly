"""Роутер статистики."""
from datetime import datetime

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, UserTimezone
from app.dto.stats import StatsResponseDTO
from app.dto.transactions import TransactionFilterDTO
from app.openapi import COMMON_ERROR_RESPONSES
from app.repositories.transaction_repository import TransactionRepository
from app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])

_AUTH_ERRORS = {401: COMMON_ERROR_RESPONSES[401]}


@router.get(
    "",
    response_model=StatsResponseDTO,
    summary="Статистика за период",
    description=(
        "Суммы доходов и расходов, разбивка расходов по категориям "
        "(для чеков — по позициям) и последние 8 расходов."
    ),
    responses={**_AUTH_ERRORS, 404: COMMON_ERROR_RESPONSES[404]},
)
def get_stats(
    db: DbSession,
    user: CurrentUser,
    tz: UserTimezone,
    from_date: datetime | None = Query(
        default=None,
        alias="from",
        description="Начало периода (YYYY-MM-DD), включительно",
    ),
    to_date: datetime | None = Query(
        default=None,
        alias="to",
        description="Конец периода (YYYY-MM-DD), включительно",
    ),
    account_id: str | None = Query(default=None, description="UUID счёта"),
) -> StatsResponseDTO:
    filters = TransactionFilterDTO(
        user_id=user.id,
        from_date=from_date,
        to_date=to_date,
        account_uid=account_id,
        timezone=tz,
    )
    return StatsService(TransactionRepository(db)).get_stats(filters)
