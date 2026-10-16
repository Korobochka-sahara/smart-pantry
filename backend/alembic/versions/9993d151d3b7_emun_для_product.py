"""emun для product

Revision ID: 9993d151d3b7
Revises: 9492265346a0
Create Date: 2026-10-16 21:17:57.728476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9993d151d3b7'
down_revision: Union[str, Sequence[str], None] = '9492265346a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Объявляем Enum заранее
unit_enum = sa.Enum('pcs', 'g', 'kg', 'ml', 'l', name='unit')


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Создаем тип в БД
    unit_enum.create(op.get_bind(), checkfirst=True)
    
    # 2. Меняем тип колонки, ЯВНО указывая, как кастовать данные (postgresql_using)
    op.alter_column('product', 'unit',
               existing_type=sa.VARCHAR(length=50),
               type_=unit_enum,
               existing_nullable=False,
               postgresql_using="unit::unit")  # <--- МАГИЯ ЗДЕСЬ
    
    op.alter_column('product', 'package_unit',
               existing_type=sa.VARCHAR(length=50),
               type_=unit_enum,
               existing_nullable=True,
               postgresql_using="package_unit::unit")  # <--- И ЗДЕСЬ


def downgrade() -> None:
    """Downgrade schema."""
    # 3. При откате возвращаем VARCHAR (тоже явно указываем каст)
    op.alter_column('product', 'package_unit',
               existing_type=unit_enum,
               type_=sa.VARCHAR(length=50),
               existing_nullable=True,
               postgresql_using="package_unit::varchar")
               
    op.alter_column('product', 'unit',
               existing_type=unit_enum,
               type_=sa.VARCHAR(length=50),
               existing_nullable=False,
               postgresql_using="unit::varchar")
               
    # 4. Удаляем тип Enum
    unit_enum.drop(op.get_bind(), checkfirst=True)