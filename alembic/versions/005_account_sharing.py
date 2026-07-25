"""Семейный доступ: role в user_accounts + account_invites."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_accounts",
        sa.Column("role", sa.String(20), nullable=False, server_default="owner"),
    )
    op.create_table(
        "account_invites",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uid", sa.String(36), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("used_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["used_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uid"),
    )
    op.create_index("ix_account_invites_uid", "account_invites", ["uid"])
    op.create_index("ix_account_invites_account_id", "account_invites", ["account_id"])
    op.create_index(
        "ix_account_invites_created_by_user_id", "account_invites", ["created_by_user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_account_invites_created_by_user_id", table_name="account_invites")
    op.drop_index("ix_account_invites_account_id", table_name="account_invites")
    op.drop_index("ix_account_invites_uid", table_name="account_invites")
    op.drop_table("account_invites")
    op.drop_column("user_accounts", "role")
