"""Роутер чеков."""
from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, UserTimezone
from app.dto.receipts import QrReceiptRequestDTO, QrReceiptResponseDTO
from app.dto.transactions import CreateTransactionFromReceiptDTO
from app.openapi import COMMON_ERROR_RESPONSES
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/receipts", tags=["receipts"])

_AUTH_ERRORS = {401: COMMON_ERROR_RESPONSES[401]}


@router.post(
    "/qr",
    response_model=QrReceiptResponseDTO,
    summary="Сканировать QR чека",
    description=(
        "Загружает чек через proverkacheka.ru, нормализует товары (AI), "
        "создаёт транзакцию-расход и списывает сумму со счёта."
    ),
    responses={
        **_AUTH_ERRORS,
        400: COMMON_ERROR_RESPONSES[400],
        404: COMMON_ERROR_RESPONSES[404],
        502: {"description": "Ошибка внешнего сервиса проверки чека"},
    },
)
def scan_qr_receipt(
    dto: QrReceiptRequestDTO, db: DbSession, user: CurrentUser, tz: UserTimezone
) -> QrReceiptResponseDTO:
    result = TransactionService(db).create_transaction_from_receipt(
        CreateTransactionFromReceiptDTO(
            user_id=user.id,
            account_uid=dto.account_id,
            qr=dto.qr,
            timezone=tz,
        )
    )
    return QrReceiptResponseDTO(transaction=result.transaction)
