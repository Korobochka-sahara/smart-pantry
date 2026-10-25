"""Allow duplicate usernames.

Revision ID: 7d1c4ab92f10
Revises: caea14f515ca
Create Date: 2026-10-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "7d1c4ab92f10"
down_revision: Union[str, Sequence[str], None] = "25132b8228e8"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # PostgreSQL's default name for this constraint is user_username_key.
    op.drop_constraint("user_username_key", "user", type_="unique")

def downgrade() -> None:
    # Downgrade can fail if duplicate usernames were registered after upgrade.
    op.create_unique_constraint("user_username_key", "user", ["username"])
