"""add household role enum

Revision ID: f490bc00d211
Revises: d15f098f1062
Create Date: 2026-09-08 21:56:51.762466
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f490bc00d211"
down_revision: Union[str, Sequence[str], None] = "d15f098f1062"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


household_role = sa.Enum(
    "OWNER",
    "ADMIN",
    "MEMBER",
    name="household_role",
)


def upgrade() -> None:
    """Upgrade schema."""

    household_role.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.alter_column(
        "household_member",
        "role",
        existing_type=sa.VARCHAR(length=50),
        type_=household_role,
        existing_nullable=False,
        postgresql_using="role::household_role",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "household_member",
        "role",
        existing_type=household_role,
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
        postgresql_using="role::VARCHAR",
    )

    household_role.drop(
        op.get_bind(),
        checkfirst=True,
    )