"""Перечисления доменной модели."""
import enum


class TransactionType(str, enum.Enum):
    EXPENSE = "expense"
    INCOME = "income"


class TransactionSource(str, enum.Enum):
    MANUAL = "manual"
    QR_RECEIPT = "qr_receipt"
    OCR = "ocr"
    IMPORT = "import"


class CategoryType(str, enum.Enum):
    EXPENSE = "expense"
    INCOME = "income"


class Currency(str, enum.Enum):
    RUB = "RUB"
