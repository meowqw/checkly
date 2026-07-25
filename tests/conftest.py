"""Общие фикстуры: SQLite in-memory + фабрики доменных объектов."""
from __future__ import annotations

from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enums import (
    AccountMemberRole,
    CategoryType,
    Currency,
    TransactionSource,
    TransactionType,
)
from app.core.security import hash_password
from app.core.uuid_utils import new_uid
from app.database import get_db
from app.database.models import (
    Account,
    Base,
    Category,
    Product,
    Transaction,
    TransactionItem,
    User,
    UserAccount,
)
from app.main import app


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # SQLite: AUTOINCREMENT только у INTEGER PK, не у BIGINT
    from sqlalchemy import BigInteger, Integer

    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, BigInteger):
                column.type = Integer()

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def user(db: Session) -> User:
    u = User(
        uid=new_uid(),
        email="demo@example.com",
        login="demo",
        password=hash_password("secret123"),
        timezone="Europe/Moscow",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def other_user(db: Session) -> User:
    u = User(
        uid=new_uid(),
        email="other@example.com",
        login="other",
        password=hash_password("secret123"),
        timezone="Europe/Moscow",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def account(db: Session, user: User) -> Account:
    acc = Account(uid=new_uid(), name="Карта", balance=100_000_00)
    db.add(acc)
    db.flush()
    db.add(
        UserAccount(
            user_id=user.id,
            account_id=acc.id,
            role=AccountMemberRole.OWNER.value,
        )
    )
    db.commit()
    db.refresh(acc)
    return acc


@pytest.fixture()
def system_categories(db: Session) -> dict[str, Category]:
    """Минимальное дерево системных категорий для тестов."""
    products = Category(
        uid=new_uid(),
        user_id=None,
        name="Продукты",
        type=CategoryType.EXPENSE.value,
        color="#16a34a",
    )
    db.add(products)
    db.flush()
    dairy = Category(
        uid=new_uid(),
        user_id=None,
        parent_id=products.id,
        name="Молочные",
        type=CategoryType.EXPENSE.value,
    )
    snacks = Category(
        uid=new_uid(),
        user_id=None,
        parent_id=products.id,
        name="Снэки",
        type=CategoryType.EXPENSE.value,
    )
    other = Category(
        uid=new_uid(),
        user_id=None,
        name="Прочее",
        type=CategoryType.EXPENSE.value,
        color="#78716c",
    )
    salary = Category(
        uid=new_uid(),
        user_id=None,
        name="Зарплата",
        type=CategoryType.INCOME.value,
        color="#16a34a",
    )
    db.add_all([dairy, snacks, other, salary])
    db.commit()
    for c in (products, dairy, snacks, other, salary):
        db.refresh(c)
    return {
        "products": products,
        "dairy": dairy,
        "snacks": snacks,
        "other": other,
        "salary": salary,
    }


def make_manual_tx(
    db: Session,
    *,
    user: User,
    account: Account,
    amount: int,
    tx_type: str = TransactionType.EXPENSE.value,
    category: Category | None = None,
    occurred_at: datetime | None = None,
    comment: str = "тест",
) -> Transaction:
    tx = Transaction(
        uid=new_uid(),
        user_id=user.id,
        account_id=account.id,
        type=tx_type,
        amount=amount,
        currency=Currency.RUB.value,
        occurred_at=occurred_at or datetime(2026, 6, 15, 12, 0, 0),
        source=TransactionSource.MANUAL.value,
        comment=comment,
    )
    db.add(tx)
    db.flush()
    db.add(
        TransactionItem(
            uid=new_uid(),
            transaction_id=tx.id,
            category_id=category.id if category else None,
            raw_name=comment,
            amount=amount,
        )
    )
    db.commit()
    db.refresh(tx)
    return tx


def make_qr_tx(
    db: Session,
    *,
    user: User,
    account: Account,
    items: list[tuple[str, int, Category | None]],
    occurred_at: datetime | None = None,
    product: Product | None = None,
) -> Transaction:
    total = sum(amount for _, amount, _ in items)
    tx = Transaction(
        uid=new_uid(),
        user_id=user.id,
        account_id=account.id,
        type=TransactionType.EXPENSE.value,
        amount=total,
        currency=Currency.RUB.value,
        occurred_at=occurred_at or datetime(2026, 6, 10, 18, 30, 0),
        source=TransactionSource.QR_RECEIPT.value,
        comment=None,
    )
    db.add(tx)
    db.flush()
    for raw_name, amount, category in items:
        db.add(
            TransactionItem(
                uid=new_uid(),
                transaction_id=tx.id,
                product_id=product.id if product else None,
                category_id=category.id if category else None,
                raw_name=raw_name,
                amount=amount,
            )
        )
    db.commit()
    db.refresh(tx)
    return tx


@pytest.fixture()
def auth_headers(user: User) -> dict[str, str]:
    from app.core.security import create_access_token

    token = create_access_token(user.uid)
    return {
        "Authorization": f"Bearer {token}",
        "X-Timezone": "Europe/Moscow",
        "Content-Type": "application/json",
    }


@pytest.fixture()
def other_auth_headers(other_user: User) -> dict[str, str]:
    from app.core.security import create_access_token

    token = create_access_token(other_user.uid)
    return {
        "Authorization": f"Bearer {token}",
        "X-Timezone": "Europe/Moscow",
        "Content-Type": "application/json",
    }
