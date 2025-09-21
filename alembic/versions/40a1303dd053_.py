"""empty message

Revision ID: 40a1303dd053
Revises: eee3075c5863
Create Date: 2025-09-21 20:33:59.894649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40a1303dd053'
down_revision: Union[str, Sequence[str], None] = 'eee3075c5863'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
