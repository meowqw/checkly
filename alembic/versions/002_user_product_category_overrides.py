"""Персональные категории товаров пользователя."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_product_category_overrides",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_user_product_override"),
    )
    op.create_index(
        "ix_user_product_category_overrides_user_id",
        "user_product_category_overrides",
        ["user_id"],
    )
    op.create_index(
        "ix_user_product_category_overrides_product_id",
        "user_product_category_overrides",
        ["product_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_product_category_overrides_product_id", "user_product_category_overrides")
    op.drop_index("ix_user_product_category_overrides_user_id", "user_product_category_overrides")
    op.drop_table("user_product_category_overrides")
