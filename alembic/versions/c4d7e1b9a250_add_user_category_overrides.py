"""add per-user category overrides and pattern ownership

Builtin categories are shared rows, so a user cannot edit them in place. This
migration adds:

* ``category_patterns.user_id`` -- NULL for the shared catalog rows, set when
  the keyword belongs to a user (their own category, or their fork of a
  builtin one).
* ``category_overrides`` -- a user's rename of a builtin category and the flag
  marking that they took over its keyword set.

Revision ID: c4d7e1b9a250
Revises: b3f1c2a4d5e6
Create Date: 2026-07-25

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d7e1b9a250"
down_revision: str | Sequence[str] | None = "b3f1c2a4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGACY_PATTERN_INDEX = "ix_category_patterns_category_id_pattern"
PATTERN_INDEX = "ix_category_patterns_category_id_user_id_pattern"


def _index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    """Add pattern ownership and the per-user override table."""
    op.add_column("category_patterns", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_category_patterns_user_id_users",
        "category_patterns",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_index("ix_category_patterns_user_id", "category_patterns", ["user_id"], unique=False)

    # Keywords of a user-owned category belong to that user.
    op.execute(
        sa.text(
            """
            UPDATE category_patterns
            SET user_id = (
                SELECT categories.user_id
                FROM categories
                WHERE categories.id = category_patterns.category_id
            )
            """
        )
    )

    # A forked keyword set repeats builtin keywords for the same category, so
    # uniqueness has to include the owner.
    if LEGACY_PATTERN_INDEX in _index_names("category_patterns"):
        op.drop_index(LEGACY_PATTERN_INDEX, table_name="category_patterns")
    op.create_index(
        PATTERN_INDEX,
        "category_patterns",
        ["category_id", "user_id", "pattern"],
        unique=True,
    )

    op.create_table(
        "category_overrides",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("patterns_overridden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "category_id", name="uq_category_overrides_user_category"),
    )
    op.create_index("ix_category_overrides_user_id", "category_overrides", ["user_id"], unique=False)
    op.create_index("ix_category_overrides_category_id", "category_overrides", ["category_id"], unique=False)


def downgrade() -> None:
    """Drop overrides and pattern ownership, keeping only the shared catalog."""
    op.drop_index("ix_category_overrides_category_id", table_name="category_overrides")
    op.drop_index("ix_category_overrides_user_id", table_name="category_overrides")
    op.drop_table("category_overrides")

    # Forked keywords have no home in the old schema.
    op.execute(sa.text("DELETE FROM category_patterns WHERE user_id IS NOT NULL"))

    if PATTERN_INDEX in _index_names("category_patterns"):
        op.drop_index(PATTERN_INDEX, table_name="category_patterns")
    op.drop_index("ix_category_patterns_user_id", table_name="category_patterns")
    op.drop_constraint("fk_category_patterns_user_id_users", "category_patterns", type_="foreignkey")
    op.drop_column("category_patterns", "user_id")
    op.create_index(
        LEGACY_PATTERN_INDEX,
        "category_patterns",
        ["category_id", "pattern"],
        unique=True,
    )
