"""add bank field to users

Revision ID: add_bank_to_users
Revises: 954559348e2e
Create Date: 2026-01-24

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_bank_to_users"
down_revision: str | Sequence[str] | None = "954559348e2e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add bank column to users table with default value."""
    op.add_column(
        "users",
        sa.Column("bank", sa.String(), nullable=False, server_default="banco_chile"),
    )


def downgrade() -> None:
    """Remove bank column from users table."""
    op.drop_column("users", "bank")
