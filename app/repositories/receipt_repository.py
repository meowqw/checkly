"""Репозиторий чеков."""
from sqlalchemy.orm import Session

from app.database.models import Receipt


class ReceiptRepository:
    def __init__(self, db: Session):
        self._db = db

    def create(self, receipt: Receipt) -> Receipt:
        self._db.add(receipt)
        self._db.flush()
        return receipt
