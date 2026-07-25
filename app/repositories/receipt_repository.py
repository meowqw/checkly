"""Репозиторий чеков."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Receipt


class ReceiptRepository:
    def __init__(self, db: Session):
        self._db = db

    def create(self, receipt: Receipt) -> Receipt:
        self._db.add(receipt)
        self._db.flush()
        return receipt

    def find_by_fiscal_ids(
        self,
        fiscal_drive_number: str,
        fiscal_document_number: str,
        fiscal_sign: str,
    ) -> Receipt | None:
        """Найти чек по фискальным реквизитам (ФН + ФД + ФП)."""
        return self._db.scalar(
            select(Receipt).where(
                Receipt.fiscal_drive_number == fiscal_drive_number,
                Receipt.fiscal_document_number == fiscal_document_number,
                Receipt.fiscal_sign == fiscal_sign,
            )
        )

    def find_by_raw_qr(self, raw_qr: str) -> Receipt | None:
        return self._db.scalar(select(Receipt).where(Receipt.raw_qr == raw_qr))
