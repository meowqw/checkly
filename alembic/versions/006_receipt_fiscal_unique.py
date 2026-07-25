"""Уникальность чека по фискальным реквизитам (ФН + ФД + ФП)."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Удаляем более поздние дубликаты (оставляем чек с минимальным id)
    # и откатываем их влияние на баланс счёта.
    dup_rows = conn.execute(
        sa.text(
            """
            SELECT r.transaction_id, t.account_id, t.amount, t.type
            FROM receipts r
            INNER JOIN transactions t ON t.id = r.transaction_id
            INNER JOIN (
                SELECT fiscal_drive_number, fiscal_document_number, fiscal_sign, MIN(id) AS keep_id
                FROM receipts
                WHERE fiscal_drive_number IS NOT NULL
                  AND fiscal_document_number IS NOT NULL
                  AND fiscal_sign IS NOT NULL
                GROUP BY fiscal_drive_number, fiscal_document_number, fiscal_sign
                HAVING COUNT(*) > 1
            ) d ON r.fiscal_drive_number = d.fiscal_drive_number
               AND r.fiscal_document_number = d.fiscal_document_number
               AND r.fiscal_sign = d.fiscal_sign
               AND r.id <> d.keep_id
            """
        )
    ).fetchall()
    for transaction_id, account_id, amount, tx_type in dup_rows:
        # expense был списан → вернуть; income был зачислен → вычесть
        if tx_type == "expense":
            conn.execute(
                sa.text("UPDATE accounts SET balance = balance + :amount WHERE id = :aid"),
                {"amount": amount, "aid": account_id},
            )
        elif tx_type == "income":
            conn.execute(
                sa.text("UPDATE accounts SET balance = balance - :amount WHERE id = :aid"),
                {"amount": amount, "aid": account_id},
            )
        conn.execute(
            sa.text("DELETE FROM transactions WHERE id = :tid"),
            {"tid": transaction_id},
        )

    op.create_unique_constraint(
        "uq_receipts_fiscal",
        "receipts",
        ["fiscal_drive_number", "fiscal_document_number", "fiscal_sign"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_receipts_fiscal", "receipts", type_="unique")
