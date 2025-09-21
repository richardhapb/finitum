"""empty message

Revision ID: eee3075c5863
Revises: fb5c529e801c
Create Date: 2025-09-21 20:29:18.635964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eee3075c5863'
down_revision: Union[str, Sequence[str], None] = 'fb5c529e801c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
