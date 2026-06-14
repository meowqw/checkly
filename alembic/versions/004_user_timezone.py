"""Часовой пояс пользователя."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Europe/Moscow"),
    )


def downgrade() -> None:
    op.drop_column("users", "timezone")
