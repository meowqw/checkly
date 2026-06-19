"""Перечисления доменной модели."""
import enum


class TransactionType(str, enum.Enum):
    """Тип транзакции."""

    EXPENSE = "expense"  # расход
    INCOME = "income"  # доход


class TransactionSource(str, enum.Enum):
    """Источник транзакции."""

    MANUAL = "manual"  # ручной ввод
    QR_RECEIPT = "qr_receipt"  # QR чека
    OCR = "ocr"  # распознавание
    IMPORT = "import"  # импорт


class CategoryType(str, enum.Enum):
    """Тип категории."""

    EXPENSE = "expense"  # расход
    INCOME = "income"  # доход


class Currency(str, enum.Enum):
    """Валюта."""

    RUB = "RUB"  # рубль
