"""merge branches

Revision ID: afda5ea8a781
Revises: 7d1c4ab92f10, 9993d151d3b7
Create Date: 2026-10-25 22:34:51.108384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afda5ea8a781'
down_revision: Union[str, Sequence[str], None] = ('7d1c4ab92f10', '9993d151d3b7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
