"""Индексы для частых фильтров списка транзакций."""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_transactions_user_occurred",
        "transactions",
        ["user_id", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_user_occurred", "transactions")
