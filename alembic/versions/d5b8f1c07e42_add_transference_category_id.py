"""point transferences at the categories catalog

Transferences stored their category as a builtin enum slug, so a user's own
category could never apply to them. This mirrors what expenses already do:
a ``category_id`` FK, backfilled from the legacy enum column.

Revision ID: d5b8f1c07e42
Revises: c4d7e1b9a250
Create Date: 2026-07-25

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d5b8f1c07e42"
down_revision: str | Sequence[str] | None = "c4d7e1b9a250"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GENERAL_CATEGORY_SLUG = "general"


def _legacy_category_type() -> sa.types.TypeEngine:
    """The pre-existing ``expensecategory`` enum, which is never dropped."""
    if op.get_bind().dialect.name == "postgresql":
        return postgresql.ENUM(name="expensecategory", create_type=False)
    return sa.String()


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _global_categories_by_slug() -> dict[str, int]:
    connection = op.get_bind()
    metadata = sa.MetaData()
    categories = sa.Table("categories", metadata, autoload_with=connection)
    return {
        row.slug: row.id
        for row in connection.execute(
            sa.select(categories.c.id, categories.c.slug).where(categories.c.user_id.is_(None))
        )
    }


def _normalize_legacy_category(value: object | None) -> str:
    if value is None:
        return GENERAL_CATEGORY_SLUG
    normalized = str(value).split(".")[-1].strip().lower()
    return normalized or GENERAL_CATEGORY_SLUG


def _backfill_transference_categories() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData()
    transferences = sa.Table("transferences", metadata, autoload_with=connection)

    categories_by_slug = _global_categories_by_slug()
    default_category_id = categories_by_slug[GENERAL_CATEGORY_SLUG]
    has_legacy_column = "category" in _column_names("transferences")

    if has_legacy_column:
        rows = connection.execute(
            sa.select(transferences.c.id, transferences.c.category, transferences.c.category_id)
        ).all()
    else:
        rows = connection.execute(sa.select(transferences.c.id, transferences.c.category_id)).all()

    for row in rows:
        if row.category_id is not None:
            continue
        slug = _normalize_legacy_category(getattr(row, "category", None))
        category_id = categories_by_slug.get(slug, default_category_id)
        connection.execute(
            transferences.update().where(transferences.c.id == row.id).values(category_id=category_id)
        )


def upgrade() -> None:
    """Add transferences.category_id, backfilled from the legacy enum."""
    if "category_id" not in _column_names("transferences"):
        op.add_column("transferences", sa.Column("category_id", sa.Integer(), nullable=True))

    _backfill_transference_categories()

    with op.batch_alter_table("transferences") as batch_op:
        batch_op.create_foreign_key(
            "fk_transferences_category_id_categories", "categories", ["category_id"], ["id"]
        )
        batch_op.create_index("ix_transferences_category_id", ["category_id"], unique=False)
        batch_op.alter_column("category_id", existing_type=sa.Integer(), nullable=False)
        if "category" in _column_names("transferences"):
            batch_op.drop_column("category")


def downgrade() -> None:
    """Restore the legacy enum column from the linked category slug."""
    if "category" not in _column_names("transferences"):
        op.add_column("transferences", sa.Column("category", _legacy_category_type(), nullable=True))

    connection = op.get_bind()
    metadata = sa.MetaData()
    transferences = sa.Table("transferences", metadata, autoload_with=connection)
    categories = sa.Table("categories", metadata, autoload_with=connection)

    slugs_by_id = {row.id: row.slug for row in connection.execute(sa.select(categories.c.id, categories.c.slug))}
    global_slugs = {
        row.slug
        for row in connection.execute(sa.select(categories.c.slug).where(categories.c.user_id.is_(None)))
    }
    for row in connection.execute(sa.select(transferences.c.id, transferences.c.category_id)):
        # Custom categories have no enum member, so they fall back to general.
        slug = slugs_by_id.get(row.category_id, GENERAL_CATEGORY_SLUG)
        if slug not in global_slugs:
            slug = GENERAL_CATEGORY_SLUG
        connection.execute(
            transferences.update().where(transferences.c.id == row.id).values(category=slug.upper())
        )

    with op.batch_alter_table("transferences") as batch_op:
        # Every row was just backfilled, so the original NOT NULL can come back.
        batch_op.alter_column("category", existing_type=_legacy_category_type(), nullable=False)
        batch_op.drop_index("ix_transferences_category_id")
        batch_op.drop_constraint("fk_transferences_category_id_categories", type_="foreignkey")
        batch_op.drop_column("category_id")
