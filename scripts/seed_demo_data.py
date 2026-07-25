"""Заполнение БД тестовыми данными для локальной разработки и бенчмарков.

Идемпотентен: если пользователь с логином ``demo`` уже есть — выходит без изменений.
Перезапись: ``python scripts/seed_demo_data.py --force``

Пример:
  docker compose exec app python scripts/seed_demo_data.py
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select

from app.core.enums import CategoryType, Currency, TransactionSource, TransactionType
from app.core.security import hash_password
from app.core.uuid_utils import new_uid
from app.database import SessionLocal
from app.database.models import (
    Account,
    Category,
    Merchant,
    Product,
    ProductAlias,
    Receipt,
    Transaction,
    TransactionItem,
    User,
    UserAccount,
    UserProductCategoryOverride,
)
from app.repositories.category_repository import CategoryRepository

DEMO_PASSWORD = "demo12345"
TIMEZONE = "Europe/Moscow"

# (login, email, accounts, manual_count, receipt_count)
USERS_SPEC = [
    ("demo", "demo@checkly.local", [("Карта", 150_000_00), ("Наличные", 25_000_00), ("Накопления", 300_000_00)], 180, 45),
    ("alice", "alice@checkly.local", [("Тинькофф", 80_000_00), ("Наличные", 5_000_00)], 60, 15),
    ("bob", "bob@checkly.local", [("Сбер", 40_000_00)], 25, 5),
]

MERCHANTS = [
    ("ООО «Пятёрочка»", "7728029110", "г. Москва, ул. Ленина, 10"),
    ("АО «Тандер» (Магнит)", "2310031475", "г. Москва, пр. Мира, 5"),
    ("ООО «ВкусВилл»", "7710667340", "г. Москва, ул. Арбат, 21"),
    ("ООО «Яндекс.Такси»", "7704340310", None),
    ("ООО «Аптека 36,6»", "7724210986", "г. Москва, ул. Тверская, 12"),
]

# (raw_name, normalized, brand, parent_cat, child_cat, price_kop)
PRODUCT_CATALOG = [
    ("Молоко домик в деревне 3.2% 1л", "Молоко 3.2%", "Домик в деревне", "Продукты", "Молочные", 8990),
    ("Хлеб белый нарезка", "Хлеб белый", None, "Продукты", "Прочее", 4500),
    ("Бананы вес", "Бананы", None, "Продукты", "Овощи и фрукты", 12990),
    ("Snickers 50г", "Snickers", "Mars", "Продукты", "Сладости", 7500),
    ("Чипсы Lays 140г", "Чипсы Lays", "Lays", "Продукты", "Снэки", 14990),
    ("Кофе Jacobs 95г", "Кофе растворимый", "Jacobs", "Продукты", "Напитки", 29990),
    ("Курица охлажд. тушка", "Курица", None, "Продукты", "Мясо и рыба", 34990),
    ("Пиво Балтика 0.5л", "Пиво Балтика", "Балтика", "Продукты", "Алкоголь", 8990),
    ("Гречка Мистраль 900г", "Гречка", "Мистраль", "Продукты", "Крупы", 11990),
    ("Вода Святой источник 1.5л", "Вода питьевая", "Святой источник", "Продукты", "Напитки", 4500),
    ("Нурофен 200мг №20", "Нурофен", "Reckitt", "Здоровье", "Аптека", 29900),
    ("Корм для кошек Whiskas", "Корм Whiskas", "Whiskas", "Животные", None, 19900),
    ("Средство Fairy 450мл", "Fairy", "Fairy", "Дом", "Бытовая химия", 18990),
    ("Сим-карта МТС", "Мобильная связь", "МТС", "Связь", "Мобильная связь", 30000),
]

MANUAL_EXPENSES = [
    ("Продукты", "Молочные", "Продукты в магазине", 450_00, 2200_00),
    ("Транспорт", "Такси", "Такси", 250_00, 900_00),
    ("Транспорт", "Общественный транспорт", "Метро", 67_00, 67_00),
    ("Развлечения", "Рестораны", "Обед в кафе", 600_00, 2500_00),
    ("Развлечения", "Подписки", "Подписка", 299_00, 799_00),
    ("Связь", "Мобильная связь", "Мобильная связь", 400_00, 800_00),
    ("Дом", "Коммунальные", "ЖКХ", 3500_00, 8500_00),
    ("Здоровье", "Аптека", "Аптека", 200_00, 1500_00),
    ("Одежда", "Одежда", "Одежда", 1500_00, 8000_00),
    ("Подарки", None, "Подарок", 1000_00, 5000_00),
    ("Животные", None, "Зоотовары", 400_00, 2000_00),
    ("Прочее", None, "Прочее", 100_00, 1500_00),
]

MANUAL_INCOMES = [
    ("Зарплата", "Зарплата", 80_000_00, 180_000_00),
    ("Подработка", "Фриланс", 5_000_00, 40_000_00),
    ("Возвраты", "Возврат", 500_00, 5_000_00),
]


def _adjust_balance(account: Account, tx_type: str, amount: int) -> None:
    if tx_type == TransactionType.EXPENSE.value:
        account.balance -= amount
    else:
        account.balance += amount


def _find_system_category(
    repo: CategoryRepository, name: str, parent_name: str | None, cat_type: str
) -> Category | None:
    parent_id = None
    if parent_name:
        parent = repo.find_system_by_name_and_type(parent_name, cat_type, None)
        if not parent:
            return None
        parent_id = parent.id
        return repo.find_system_by_name_and_type(name, cat_type, parent_id)
    return repo.find_system_by_name_and_type(name, cat_type, None)


def _resolve_category(
    repo: CategoryRepository, parent: str, child: str | None, cat_type: str
) -> Category | None:
    if child:
        found = _find_system_category(repo, child, parent, cat_type)
        if found:
            return found
    return _find_system_category(repo, parent, None, cat_type)


def _wipe_demo_users(db) -> int:
    logins = [spec[0] for spec in USERS_SPEC]
    users = list(db.scalars(select(User).where(User.login.in_(logins))).all())
    if not users:
        return 0

    user_ids = [u.id for u in users]
    account_ids = list(
        db.scalars(
            select(UserAccount.account_id).where(UserAccount.user_id.in_(user_ids))
        ).all()
    )

    db.execute(
        delete(UserProductCategoryOverride).where(
            UserProductCategoryOverride.user_id.in_(user_ids)
        )
    )
    # транзакции/чеки/позиции каскадом с users; счета — после user_accounts
    for user in users:
        db.delete(user)
    db.flush()

    if account_ids:
        orphan_accounts = list(
            db.scalars(
                select(Account).where(Account.id.in_(account_ids)).where(
                    ~Account.id.in_(select(UserAccount.account_id))
                )
            ).all()
        )
        for acc in orphan_accounts:
            db.delete(acc)

    db.commit()
    return len(users)


def _ensure_merchants(db) -> list[Merchant]:
    result: list[Merchant] = []
    for name, inn, address in MERCHANTS:
        existing = db.scalar(select(Merchant).where(Merchant.inn == inn))
        if existing:
            result.append(existing)
            continue
        m = Merchant(uid=new_uid(), name=name, inn=inn, address=address)
        db.add(m)
        db.flush()
        result.append(m)
    return result


def _ensure_products(db, cat_repo: CategoryRepository) -> list[tuple[Product, int]]:
    """Возвращает список (product, typical_price_kop)."""
    result: list[tuple[Product, int]] = []
    for raw, normalized, brand, parent, child, price in PRODUCT_CATALOG:
        existing = db.scalar(
            select(Product).where(Product.normalized_name == normalized)
        )
        if existing:
            result.append((existing, price))
            continue
        cat = _resolve_category(cat_repo, parent, child, CategoryType.EXPENSE.value)
        product = Product(
            uid=new_uid(),
            name=normalized,
            normalized_name=normalized,
            brand=brand,
            category_id=cat.id if cat else None,
        )
        db.add(product)
        db.flush()
        alias = ProductAlias(
            uid=new_uid(),
            product_id=product.id,
            merchant_id=None,
            raw_name=raw,
            normalized_name=normalized,
            confidence=0.95,
        )
        db.add(alias)
        result.append((product, price))
    return result


def _seed_user(
    db,
    cat_repo: CategoryRepository,
    login: str,
    email: str,
    accounts_spec: list[tuple[str, int]],
    manual_count: int,
    receipt_count: int,
    merchants: list[Merchant],
    products: list[tuple[Product, int]],
    rng: random.Random,
) -> User:
    user = User(
        uid=new_uid(),
        email=email,
        login=login,
        password=hash_password(DEMO_PASSWORD),
        timezone=TIMEZONE,
    )
    db.add(user)
    db.flush()

    accounts: list[Account] = []
    for name, balance in accounts_spec:
        acc = Account(uid=new_uid(), name=name, balance=balance)
        db.add(acc)
        db.flush()
        db.add(UserAccount(user_id=user.id, account_id=acc.id))
        accounts.append(acc)

    # Пользовательская категория (только для demo)
    if login == "demo":
        custom = Category(
            uid=new_uid(),
            user_id=user.id,
            parent_id=None,
            name="Хобби (своя)",
            type=CategoryType.EXPENSE.value,
            icon="palette",
            color="#0d9488",
        )
        db.add(custom)
        db.flush()
        hobby_amount = 2_500_00
        tx = Transaction(
            uid=new_uid(),
            user_id=user.id,
            account_id=accounts[0].id,
            type=TransactionType.EXPENSE.value,
            amount=hobby_amount,
            currency=Currency.RUB.value,
            occurred_at=datetime.now().replace(microsecond=0) - timedelta(days=3),
            source=TransactionSource.MANUAL.value,
            comment="Кисти и краски",
        )
        db.add(tx)
        db.flush()
        db.add(
            TransactionItem(
                uid=new_uid(),
                transaction_id=tx.id,
                category_id=custom.id,
                raw_name="Кисти и краски",
                amount=hobby_amount,
            )
        )
        _adjust_balance(accounts[0], TransactionType.EXPENSE.value, hobby_amount)

    now = datetime.now().replace(microsecond=0)
    for i in range(manual_count):
        days_ago = rng.randint(0, 180)
        occurred = now - timedelta(days=days_ago, hours=rng.randint(8, 21), minutes=rng.randint(0, 59))
        account = rng.choice(accounts)

        if rng.random() < 0.18:
            parent, comment, lo, hi = rng.choice(MANUAL_INCOMES)
            amount = rng.randint(lo, hi)
            cat = _resolve_category(cat_repo, parent, None, CategoryType.INCOME.value)
            tx_type = TransactionType.INCOME.value
        else:
            parent, child, comment, lo, hi = rng.choice(MANUAL_EXPENSES)
            amount = rng.randint(lo, hi)
            cat = _resolve_category(cat_repo, parent, child, CategoryType.EXPENSE.value)
            tx_type = TransactionType.EXPENSE.value

        tx = Transaction(
            uid=new_uid(),
            user_id=user.id,
            account_id=account.id,
            type=tx_type,
            amount=amount,
            currency=Currency.RUB.value,
            occurred_at=occurred,
            source=TransactionSource.MANUAL.value,
            comment=comment,
        )
        db.add(tx)
        db.flush()
        db.add(
            TransactionItem(
                uid=new_uid(),
                transaction_id=tx.id,
                category_id=cat.id if cat else None,
                raw_name=comment,
                amount=amount,
            )
        )
        _adjust_balance(account, tx_type, amount)

    for i in range(receipt_count):
        days_ago = rng.randint(0, 120)
        occurred = now - timedelta(days=days_ago, hours=rng.randint(10, 20), minutes=rng.randint(0, 59))
        account = accounts[0]
        merchant = rng.choice(merchants)
        item_count = rng.randint(2, 7)
        chosen = rng.sample(products, k=min(item_count, len(products)))

        items_data: list[tuple[Product, str, int, int]] = []
        total = 0
        for product, price in chosen:
            qty = rng.randint(1, 3)
            amount = price * qty
            total += amount
            raw = next(
                (p[0] for p in PRODUCT_CATALOG if p[1] == product.normalized_name),
                product.name,
            )
            items_data.append((product, raw, qty, amount))

        tx = Transaction(
            uid=new_uid(),
            user_id=user.id,
            account_id=account.id,
            merchant_id=merchant.id,
            type=TransactionType.EXPENSE.value,
            amount=total,
            currency=Currency.RUB.value,
            occurred_at=occurred,
            source=TransactionSource.QR_RECEIPT.value,
            comment=None,
        )
        db.add(tx)
        db.flush()

        for product, raw, qty, amount in items_data:
            db.add(
                TransactionItem(
                    uid=new_uid(),
                    transaction_id=tx.id,
                    product_id=product.id,
                    category_id=product.category_id,
                    raw_name=raw,
                    quantity=qty,
                    price=amount // qty if qty else amount,
                    amount=amount,
                )
            )

        fd = f"9999{rng.randint(100000, 999999)}"
        fn = str(rng.randint(10000, 99999))
        fp = str(rng.randint(100000000, 999999999))
        db.add(
            Receipt(
                uid=new_uid(),
                transaction_id=tx.id,
                fiscal_drive_number=fd,
                fiscal_document_number=fn,
                fiscal_sign=fp,
                operation_type=1,
                receipt_datetime=occurred,
                total_sum=total,
                raw_qr=f"t={occurred.strftime('%Y%m%dT%H%M')}&s={total / 100:.2f}&fn={fd}&i={fn}&fp={fp}&n=1",
                raw_json={"seed": True, "merchant": merchant.name, "total": total},
            )
        )
        _adjust_balance(account, TransactionType.EXPENSE.value, total)

    # Персональный override категории для demo
    if login == "demo" and products:
        product, _ = products[0]
        prochee = _resolve_category(cat_repo, "Прочее", None, CategoryType.EXPENSE.value)
        if product and prochee:
            existing_ov = db.scalar(
                select(UserProductCategoryOverride).where(
                    UserProductCategoryOverride.user_id == user.id,
                    UserProductCategoryOverride.product_id == product.id,
                )
            )
            if not existing_ov:
                db.add(
                    UserProductCategoryOverride(
                        user_id=user.id,
                        product_id=product.id,
                        category_id=prochee.id,
                    )
                )

    return user


def seed(*, force: bool = False) -> None:
    db = SessionLocal()
    try:
        cat_repo = CategoryRepository(db)
        existing = db.scalar(select(User).where(User.login == "demo"))
        if existing and not force:
            print("Демо-данные уже есть (login=demo). Используйте --force для пересоздания.")
            return
        if existing and force:
            wiped = _wipe_demo_users(db)
            print(f"Удалено демо-пользователей: {wiped}")

        # Убедимся, что системные категории есть
        if not cat_repo.find_system_by_name_and_type("Продукты", CategoryType.EXPENSE.value):
            print("Сначала запустите: python scripts/seed_categories.py")
            return

        rng = random.Random(42)
        merchants = _ensure_merchants(db)
        products = _ensure_products(db, cat_repo)

        for login, email, accounts_spec, manual_n, receipt_n in USERS_SPEC:
            _seed_user(
                db,
                cat_repo,
                login,
                email,
                accounts_spec,
                manual_n,
                receipt_n,
                merchants,
                products,
                rng,
            )
            print(f"  + {login} / {email}  (пароль: {DEMO_PASSWORD})")

        db.commit()

        # Сводка
        print("\nГотово. Сводка:")
        for login, *_ in USERS_SPEC:
            user = db.scalar(select(User).where(User.login == login))
            if not user:
                continue
            n_tx = len(list(db.scalars(select(Transaction).where(Transaction.user_id == user.id))))
            n_acc = len(list(db.scalars(
                select(Account)
                .join(UserAccount, UserAccount.account_id == Account.id)
                .where(UserAccount.user_id == user.id)
            )))
            print(f"  {login}: счетов={n_acc}, транзакций={n_tx}")
        print(f"\nЛогин для бенчмарка: demo / {DEMO_PASSWORD}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Сидер тестовых данных Finance Manager")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Удалить демо-пользователей и создать заново",
    )
    args = parser.parse_args()
    seed(force=args.force)


if __name__ == "__main__":
    main()
