"""add categories catalog and expense category id

Revision ID: 6f2d3f6b9d1a
Revises: 209481f76956
Create Date: 2026-03-02 13:10:00.000000

"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f2d3f6b9d1a"
down_revision: str | Sequence[str] | None = "209481f76956"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


GENERAL_CATEGORY_SLUG = "general"

PARSER_CATEGORY_TO_SLUG: dict[str, str] = {
    "Food": "food",
    "Education": "education",
    "Transport": "transport",
    "Services": "services",
    "Transfers": "transfers",
    "Clothing": "clothing",
    "Entertainment": "entertainment",
    "Sports": "sports",
    "Loan": "loan",
    "ATM_withdrawal": "atm_withdrawal",
    "Investments": "investments",
    "Housing": "housing",
    "External_food": "external_food",
    "Recreation": "recreation",
    "Online": "online",
    "Commissions": "commissions",
    "Travel": "travel",
    "Health": "health",
    "Family": "family",
    "Laundry": "laundry",
    "Books": "books",
    "Purified_water": "purified_water",
}

ENGLISH_LABELS_BY_SLUG: dict[str, str] = {
    GENERAL_CATEGORY_SLUG: "Other",
    "food": "Food",
    "education": "Education",
    "transport": "Transport",
    "services": "Services",
    "transfers": "Transfers",
    "clothing": "Clothing",
    "entertainment": "Entertainment",
    "sports": "Sports",
    "loan": "Loan",
    "atm_withdrawal": "ATM Withdrawal",
    "investments": "Investments",
    "housing": "Housing",
    "external_food": "Restaurants",
    "recreation": "Recreation",
    "online": "Online",
    "commissions": "Commissions",
    "travel": "Travel",
    "health": "Health",
    "family": "Family",
    "laundry": "Laundry",
    "books": "Books",
    "purified_water": "Purified Water",
}

EXPENSE_ENUM_VALUES = (
    "GENERAL",
    "FOOD",
    "EDUCATION",
    "TRANSPORT",
    "SERVICES",
    "TRANSFERS",
    "CLOTHING",
    "ENTERTAINMENT",
    "SPORTS",
    "LOAN",
    "ATM_WITHDRAWAL",
    "INVESTMENTS",
    "HOUSING",
    "EXTERNAL_FOOD",
    "RECREATION",
    "ONLINE",
    "COMMISSIONS",
    "TRAVEL",
    "HEALTH",
    "FAMILY",
    "LAUNDRY",
    "BOOKS",
    "PURIFIED_WATER",
)

CATEGORY_ENUM = sa.Enum(*EXPENSE_ENUM_VALUES, name="expensecategory")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as file_obj:
        data = json.load(file_obj)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _get_builtin_rows() -> list[dict[str, object]]:
    keywords_by_parser = _load_json(_repo_root() / "categories.json")
    labels_es = _load_json(_repo_root() / "category_labels.es.json")

    rows: list[dict[str, object]] = [
        {
            "slug": GENERAL_CATEGORY_SLUG,
            "name_en": ENGLISH_LABELS_BY_SLUG[GENERAL_CATEGORY_SLUG],
            "name_es": str(labels_es[GENERAL_CATEGORY_SLUG]),
            "patterns": [],
        }
    ]

    for parser_key, slug in PARSER_CATEGORY_TO_SLUG.items():
        patterns = keywords_by_parser.get(parser_key, [])
        if not isinstance(patterns, list):
            raise ValueError(f"Expected keyword list for parser category {parser_key}")

        rows.append(
            {
                "slug": slug,
                "name_en": ENGLISH_LABELS_BY_SLUG[slug],
                "name_es": str(labels_es[slug]),
                "patterns": [str(pattern) for pattern in patterns],
            }
        )

    return rows


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in _inspector().get_columns(table_name)}


def _create_category_tables() -> None:
    inspector = _inspector()

    if not inspector.has_table("categories"):
        op.create_table(
            "categories",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("slug", sa.String(), nullable=False),
            sa.Column("name_en", sa.String(), nullable=False),
            sa.Column("name_es", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)
        op.create_index("ix_categories_user_id", "categories", ["user_id"], unique=False)

    inspector = _inspector()
    if not inspector.has_table("category_patterns"):
        op.create_table(
            "category_patterns",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("category_id", sa.Integer(), nullable=False),
            sa.Column("pattern", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_category_patterns_category_id_pattern",
            "category_patterns",
            ["category_id", "pattern"],
            unique=True,
        )


def _seed_builtin_categories() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData()
    categories = sa.Table("categories", metadata, autoload_with=connection)
    category_patterns = sa.Table("category_patterns", metadata, autoload_with=connection)

    existing_categories = {
        row.slug: row.id
        for row in connection.execute(
            sa.select(categories.c.id, categories.c.slug).where(categories.c.user_id.is_(None))
        )
    }

    for row in _get_builtin_rows():
        if row["slug"] in existing_categories:
            continue
        result = connection.execute(
            categories.insert().values(
                user_id=None,
                slug=row["slug"],
                name_en=row["name_en"],
                name_es=row["name_es"],
            )
        )
        existing_categories[str(row["slug"])] = result.inserted_primary_key[0]

    existing_pattern_keys = {
        (row.category_id, row.pattern)
        for row in connection.execute(sa.select(category_patterns.c.category_id, category_patterns.c.pattern))
    }

    for row in _get_builtin_rows():
        category_id = existing_categories[str(row["slug"])]
        for pattern in row["patterns"]:
            key = (category_id, pattern)
            if key in existing_pattern_keys:
                continue
            connection.execute(category_patterns.insert().values(category_id=category_id, pattern=pattern))
            existing_pattern_keys.add(key)


def _normalize_legacy_category(value: object | None) -> str:
    if value is None:
        return GENERAL_CATEGORY_SLUG
    normalized = str(value).split(".")[-1].strip().lower()
    return normalized or GENERAL_CATEGORY_SLUG


def _backfill_expense_categories() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData()
    categories = sa.Table("categories", metadata, autoload_with=connection)
    expenses = sa.Table("expenses", metadata, autoload_with=connection)
    expense_columns = _column_names("expenses")

    categories_by_slug = {
        row.slug: row.id
        for row in connection.execute(
            sa.select(categories.c.id, categories.c.slug).where(categories.c.user_id.is_(None))
        )
    }
    default_category_id = categories_by_slug[GENERAL_CATEGORY_SLUG]

    if "category" in expense_columns:
        rows = connection.execute(sa.select(expenses.c.id, expenses.c.category, expenses.c.category_id)).all()
    else:
        rows = connection.execute(sa.select(expenses.c.id, expenses.c.category_id)).all()

    for row in rows:
        if row.category_id is not None:
            continue

        slug = _normalize_legacy_category(getattr(row, "category", None))
        category_id = categories_by_slug.get(slug, default_category_id)
        connection.execute(
            expenses.update().where(expenses.c.id == row.id).values(category_id=category_id)
        )


def upgrade() -> None:
    """Upgrade schema."""
    _create_category_tables()
    _seed_builtin_categories()

    if "category_id" not in _column_names("expenses"):
        op.add_column("expenses", sa.Column("category_id", sa.Integer(), nullable=True))

    _backfill_expense_categories()

    index_names = {index["name"] for index in _inspector().get_indexes("expenses")}
    has_category_fk = any(
        foreign_key["referred_table"] == "categories"
        and foreign_key["constrained_columns"] == ["category_id"]
        for foreign_key in _inspector().get_foreign_keys("expenses")
    )

    with op.batch_alter_table("expenses") as batch_op:
        if not has_category_fk:
            batch_op.create_foreign_key("fk_expenses_category_id_categories", "categories", ["category_id"], ["id"])
        if "ix_expenses_category_id" not in index_names:
            batch_op.create_index("ix_expenses_category_id", ["category_id"], unique=False)
        batch_op.alter_column("category_id", existing_type=sa.Integer(), nullable=False)
        if "category" in _column_names("expenses"):
            batch_op.drop_column("category")


def downgrade() -> None:
    """Downgrade schema."""
    if "category" not in _column_names("expenses"):
        op.add_column("expenses", sa.Column("category", CATEGORY_ENUM, nullable=True))

    connection = op.get_bind()
    metadata = sa.MetaData()
    categories = sa.Table("categories", metadata, autoload_with=connection)
    expenses = sa.Table("expenses", metadata, autoload_with=connection)

    categories_by_id = {
        row.id: row.slug
        for row in connection.execute(sa.select(categories.c.id, categories.c.slug))
    }

    for row in connection.execute(sa.select(expenses.c.id, expenses.c.category_id)):
        slug = categories_by_id.get(row.category_id, GENERAL_CATEGORY_SLUG)
        connection.execute(
            expenses.update().where(expenses.c.id == row.id).values(category=slug.upper())
        )

    index_names = {index["name"] for index in _inspector().get_indexes("expenses")}
    fk_names = {foreign_key["name"] for foreign_key in _inspector().get_foreign_keys("expenses")}

    with op.batch_alter_table("expenses") as batch_op:
        batch_op.alter_column("category", existing_type=CATEGORY_ENUM, nullable=False)
        if "ix_expenses_category_id" in index_names:
            batch_op.drop_index("ix_expenses_category_id")
        if "fk_expenses_category_id_categories" in fk_names:
            batch_op.drop_constraint("fk_expenses_category_id_categories", type_="foreignkey")
        batch_op.drop_column("category_id")

    if _inspector().has_table("category_patterns"):
        op.drop_table("category_patterns")

    if _inspector().has_table("categories"):
        op.drop_table("categories")
