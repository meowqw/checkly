"""Плоские категории + независимые теги: миграция данных и схемы."""
from datetime import datetime
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tags",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uid", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("icon", sa.String(length=100), nullable=True),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tags_uid", "tags", ["uid"], unique=True)
    op.create_index("ix_tags_user_id", "tags", ["user_id"], unique=False)

    op.create_table(
        "transaction_item_tags",
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("tag_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["transaction_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("item_id", "tag_id"),
    )

    conn = op.get_bind()
    now = datetime.utcnow()

    def _ensure_tag(name: str, user_id: int | None, cache: dict[tuple, int]) -> int:
        key = (user_id, name)
        if key in cache:
            return cache[key]
        existing = conn.execute(
            sa.text(
                "SELECT id FROM tags WHERE name = :name AND "
                + ("user_id IS NULL" if user_id is None else "user_id = :user_id")
            ),
            {"name": name, "user_id": user_id},
        ).scalar()
        if existing:
            cache[key] = int(existing)
            return int(existing)
        tag_uid = str(uuid4())
        conn.execute(
            sa.text(
                """
                INSERT INTO tags (uid, user_id, name, icon, color, created_at, updated_at)
                VALUES (:uid, :user_id, :name, NULL, NULL, :now, :now)
                """
            ),
            {"uid": tag_uid, "user_id": user_id, "name": name, "now": now},
        )
        tag_id = conn.execute(
            sa.text("SELECT id FROM tags WHERE uid = :uid"),
            {"uid": tag_uid},
        ).scalar_one()
        cache[key] = int(tag_id)
        return int(tag_id)

    def _migrate_child(child_id: int, parent_id: int, tag_id: int) -> None:
        # Привязать тег к позициям (идемпотентно)
        item_ids = conn.execute(
            sa.text("SELECT id FROM transaction_items WHERE category_id = :cid"),
            {"cid": child_id},
        ).fetchall()
        for (item_id,) in item_ids:
            exists = conn.execute(
                sa.text(
                    "SELECT 1 FROM transaction_item_tags WHERE item_id = :iid AND tag_id = :tid"
                ),
                {"iid": item_id, "tid": tag_id},
            ).scalar()
            if not exists:
                conn.execute(
                    sa.text(
                        "INSERT INTO transaction_item_tags (item_id, tag_id) VALUES (:iid, :tid)"
                    ),
                    {"iid": item_id, "tid": tag_id},
                )
        conn.execute(
            sa.text(
                "UPDATE transaction_items SET category_id = :pid WHERE category_id = :cid"
            ),
            {"pid": parent_id, "cid": child_id},
        )
        conn.execute(
            sa.text("UPDATE products SET category_id = :pid WHERE category_id = :cid"),
            {"pid": parent_id, "cid": child_id},
        )
        conn.execute(
            sa.text(
                "UPDATE user_product_category_overrides SET category_id = :pid WHERE category_id = :cid"
            ),
            {"pid": parent_id, "cid": child_id},
        )

    tag_cache: dict[tuple, int] = {}
    children = conn.execute(
        sa.text(
            """
            SELECT id, name, parent_id, user_id
            FROM categories
            WHERE parent_id IS NOT NULL
            """
        )
    ).fetchall()
    for child_id, name, parent_id, user_id in children:
        tag_id = _ensure_tag(name, user_id, tag_cache)
        _migrate_child(int(child_id), int(parent_id), tag_id)

    conn.execute(sa.text("DELETE FROM categories WHERE parent_id IS NOT NULL"))

    # Снять FK parent_id независимо от имени constraint
    inspector = sa.inspect(conn)
    for fk in inspector.get_foreign_keys("categories"):
        if fk.get("constrained_columns") == ["parent_id"] and fk.get("name"):
            op.drop_constraint(fk["name"], "categories", type_="foreignkey")
            break

    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_column("categories", "parent_id")


def downgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"], unique=False)
    op.create_foreign_key(
        "fk_categories_parent_id",
        "categories",
        "categories",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_table("transaction_item_tags")
    op.drop_index("ix_tags_user_id", table_name="tags")
    op.drop_index("ix_tags_uid", table_name="tags")
    op.drop_table("tags")
