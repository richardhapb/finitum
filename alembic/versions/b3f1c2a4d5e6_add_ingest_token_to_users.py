"""add ingest_token to users

Revision ID: b3f1c2a4d5e6
Revises: 157ca74e3e8a
Create Date: 2026-06-10

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3f1c2a4d5e6"
down_revision: str | Sequence[str] | None = "157ca74e3e8a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add nullable, unique ingest_token column for forwarding ingestion."""
    op.add_column("users", sa.Column("ingest_token", sa.String(), nullable=True))
    op.create_index("ix_users_ingest_token", "users", ["ingest_token"], unique=True)


def downgrade() -> None:
    """Remove ingest_token column and its unique index."""
    op.drop_index("ix_users_ingest_token", table_name="users")
    op.drop_column("users", "ingest_token")
