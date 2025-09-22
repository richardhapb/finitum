"""initial

Revision ID: 432dcd797b7e
Revises: 40a1303dd053
Create Date: 2025-09-21 20:39:53.889134

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "432dcd797b7e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with open("alembic/initial.sql") as file:
        op.execute(file.read())


def downgrade() -> None:
    """Downgrade schema."""
    pass
