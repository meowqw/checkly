"""Интерфейс провайдера данных чека."""
from abc import ABC, abstractmethod

from app.dto.receipts import ReceiptProviderInputDTO, ReceiptProviderOutputDTO


class ReceiptProviderInterface(ABC):
    @abstractmethod
    def get_receipt_by_qr(self, dto: ReceiptProviderInputDTO) -> ReceiptProviderOutputDTO:
        """Получить данные фискального чека по QR-строке."""
