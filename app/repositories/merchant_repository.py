"""Репозиторий продавцов."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Merchant


class MerchantRepository:
    def __init__(self, db: Session):
        self._db = db

    def find_by_inn(self, inn: str | None) -> Merchant | None:
        if not inn:
            return None
        return self._db.scalar(select(Merchant).where(Merchant.inn == inn))

    def find_by_name(self, name: str) -> Merchant | None:
        return self._db.scalar(select(Merchant).where(Merchant.name == name))

    def create(self, merchant: Merchant) -> Merchant:
        self._db.add(merchant)
        self._db.flush()
        return merchant
