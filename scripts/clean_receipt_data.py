"""Очистка товаров и/или транзакций из QR-чеков для повторного теста нормализации.

Примеры:
  python scripts/clean_receipt_data.py --all
  python scripts/clean_receipt_data.py --products
  python scripts/clean_receipt_data.py --qr-transactions
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select

from app.core.enums import TransactionSource, TransactionType
from app.database import SessionLocal
from app.database.models import Account, Product, ProductAlias, Receipt, Transaction


def clean_products(db) -> tuple[int, int]:
    aliases = db.execute(delete(ProductAlias)).rowcount or 0
    products = db.execute(delete(Product)).rowcount or 0
    return aliases, products


def clean_qr_transactions(db, user_id: int | None = None) -> int:
    stmt = select(
        Transaction.id,
        Transaction.account_id,
        Transaction.type,
        Transaction.amount,
    ).where(Transaction.source == TransactionSource.QR_RECEIPT.value)
    if user_id is not None:
        stmt = stmt.where(Transaction.user_id == user_id)

    rows = db.execute(stmt).all()
    if not rows:
        return 0

    tx_ids = [row.id for row in rows]

    for row in rows:
        account = db.get(Account, row.account_id)
        if not account:
            continue
        if row.type == TransactionType.EXPENSE.value:
            account.balance += row.amount
        else:
            account.balance -= row.amount

    db.execute(delete(Receipt).where(Receipt.transaction_id.in_(tx_ids)))
    db.execute(delete(Transaction).where(Transaction.id.in_(tx_ids)))
    return len(tx_ids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Очистка данных чеков для повторного теста")
    parser.add_argument(
        "--products",
        action="store_true",
        help="Удалить все products и product_aliases",
    )
    parser.add_argument(
        "--qr-transactions",
        action="store_true",
        help="Удалить транзакции qr_receipt и вернуть суммы на счета",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Удалить и транзакции, и товары (рекомендуется перед повторным сканом)",
    )
    args = parser.parse_args()

    if not args.products and not args.qr_transactions and not args.all:
        parser.error("Укажите --products, --qr-transactions или --all")

    do_products = args.products or args.all
    do_qr = args.qr_transactions or args.all

    db = SessionLocal()
    try:
        if do_qr:
            count = clean_qr_transactions(db)
            print(f"Удалено QR-транзакций: {count} (баланс счетов восстановлен)")

        if do_products:
            aliases, products = clean_products(db)
            print(f"Удалено алиасов товаров: {aliases}")
            print(f"Удалено товаров: {products}")

        db.commit()
        print("Готово. Можно снова сканировать чек.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
