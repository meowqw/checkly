"""Роутер чеков."""
from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.dto.receipts import QrReceiptRequestDTO, QrReceiptResponseDTO
from app.dto.transactions import CreateTransactionFromReceiptDTO, TransactionResponseDTO
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("/qr", response_model=QrReceiptResponseDTO)
def scan_qr_receipt(
    dto: QrReceiptRequestDTO, db: DbSession, user: CurrentUser
) -> QrReceiptResponseDTO:
    result = TransactionService(db).create_transaction_from_receipt(
        CreateTransactionFromReceiptDTO(
            user_id=user.id,
            account_uid=dto.account_id,
            qr=dto.qr,
        )
    )
    return QrReceiptResponseDTO(transaction=result.transaction)
