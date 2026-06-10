"""encrypt google credentials and drop client_secret

Revision ID: 157ca74e3e8a
Revises: 6f2d3f6b9d1a
Create Date: 2026-06-10 00:09:21.491331

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from utils.crypto import decrypt, encrypt

# revision identifiers, used by Alembic.
revision: str = "157ca74e3e8a"
down_revision: str | Sequence[str] | None = "6f2d3f6b9d1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Sensitive fields persisted on user_google_credentials that are encrypted at rest.
_ENCRYPTED_COLUMNS = ("token", "refresh_token", "id_token")


def _credentials_table() -> sa.Table:
    return sa.table(
        "user_google_credentials",
        sa.column("id", sa.Integer),
        sa.column("token", sa.Text),
        sa.column("refresh_token", sa.Text),
        sa.column("id_token", sa.Text),
    )


def upgrade() -> None:
    """Encrypt existing plaintext credential columns, then drop client_secret."""
    bind = op.get_bind()
    table = _credentials_table()

    rows = bind.execute(sa.select(table.c.id, table.c.token, table.c.refresh_token, table.c.id_token)).fetchall()
    for row in rows:
        values = {col: encrypt(getattr(row, col)) for col in _ENCRYPTED_COLUMNS}
        bind.execute(table.update().where(table.c.id == row.id).values(**values))

    op.drop_column("user_google_credentials", "client_secret")


def downgrade() -> None:
    """Restore client_secret column and decrypt credential columns back to plaintext."""
    op.add_column(
        "user_google_credentials",
        sa.Column("client_secret", sa.Text(), nullable=False, server_default=""),
    )

    bind = op.get_bind()
    table = _credentials_table()

    rows = bind.execute(sa.select(table.c.id, table.c.token, table.c.refresh_token, table.c.id_token)).fetchall()
    for row in rows:
        values = {col: decrypt(getattr(row, col)) for col in _ENCRYPTED_COLUMNS}
        bind.execute(table.update().where(table.c.id == row.id).values(**values))
