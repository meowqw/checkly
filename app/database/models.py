"""SQLAlchemy-модели домена."""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="Europe/Moscow", server_default="Europe/Moscow"
    )

    accounts: Mapped[list["Account"]] = relationship(
        "Account", secondary="user_accounts", back_populates="users"
    )
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="user")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="user")


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    users: Mapped[list["User"]] = relationship(
        "User", secondary="user_accounts", back_populates="accounts"
    )
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="account")


class UserAccount(Base):
    __tablename__ = "user_accounts"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="owner", server_default="owner"
    )


class AccountInvite(Base, TimestampMixin):
    """Одноразовый инвайт на совместный доступ к счёту."""

    __tablename__ = "account_invites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    used_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    account: Mapped["Account"] = relationship("Account")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    used_by: Mapped["User | None"] = relationship("User", foreign_keys=[used_by_user_id])


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    user: Mapped["User | None"] = relationship("User", back_populates="categories")
    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side="Category.id", back_populates="children"  # type: ignore[arg-type]
    )
    children: Mapped[list["Category"]] = relationship("Category", back_populates="parent")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


class Merchant(Base, TimestampMixin):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    inn: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="merchant")
    product_aliases: Mapped[list["ProductAlias"]] = relationship(
        "ProductAlias", back_populates="merchant"
    )


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gtin: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    category: Mapped["Category | None"] = relationship("Category", back_populates="products")
    aliases: Mapped[list["ProductAlias"]] = relationship("ProductAlias", back_populates="product")
    transaction_items: Mapped[list["TransactionItem"]] = relationship(
        "TransactionItem", back_populates="product"
    )


class ProductAlias(Base, TimestampMixin):
    __tablename__ = "product_aliases"
    __table_args__ = (
        Index("ix_product_aliases_raw_merchant", "raw_name", "merchant_id"),
        Index("ix_product_aliases_normalized", "normalized_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    merchant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True
    )
    raw_name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="aliases")
    merchant: Mapped["Merchant | None"] = relationship("Merchant", back_populates="product_aliases")


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    merchant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="RUB", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="transactions")
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    merchant: Mapped["Merchant | None"] = relationship("Merchant", back_populates="transactions")
    items: Mapped[list["TransactionItem"]] = relationship(
        "TransactionItem", back_populates="transaction", cascade="all, delete-orphan"
    )
    receipt: Mapped["Receipt | None"] = relationship(
        "Receipt", back_populates="transaction", uselist=False
    )


class TransactionItem(Base, TimestampMixin):
    __tablename__ = "transaction_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    transaction_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    raw_name: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="items")
    product: Mapped["Product | None"] = relationship("Product", back_populates="transaction_items")
    category: Mapped["Category | None"] = relationship("Category")


class UserProductCategoryOverride(Base, TimestampMixin):
    """Персональная категория товара для пользователя (не меняет глобальный Product)."""

    __tablename__ = "user_product_category_overrides"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_user_product_override"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship("User")
    product: Mapped["Product"] = relationship("Product")
    category: Mapped["Category"] = relationship("Category")


class Receipt(Base, TimestampMixin):
    __tablename__ = "receipts"
    __table_args__ = (
        UniqueConstraint(
            "fiscal_drive_number",
            "fiscal_document_number",
            "fiscal_sign",
            name="uq_receipts_fiscal",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    transaction_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("transactions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    fiscal_drive_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fiscal_document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fiscal_sign: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operation_type: Mapped[int | None] = mapped_column(Integer, nullable=True)
    receipt_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_sum: Mapped[int] = mapped_column(BigInteger, nullable=False)
    raw_qr: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="receipt")
