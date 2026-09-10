"""remove inventory_event and upgrate inventory_item

Revision ID: e6ef66e5f375
Revises: 2a17cf716572
Create Date: 2026-09-10 15:08:38.915267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e6ef66e5f375'
down_revision: Union[str, Sequence[str], None] = '2a17cf716572'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Сначала создаем ENUM тип в PostgreSQL
    op.execute("""
        CREATE TYPE product_category AS ENUM (
            'dairy', 'meat', 'fish', 'vegetables', 'fruits', 
            'groceries', 'drinks', 'frozen', 'sweets', 'other'
        )
    """)

    # 2. Выполняем остальные изменения
    op.drop_index(op.f('ix_inventory_events_item'), table_name='inventory_event')
    op.drop_table('inventory_event')
    op.drop_index(op.f('ix_inventory_household_product'), table_name='inventory_item')
    op.create_unique_constraint('uq_inventory_household_product', 'inventory_item', ['household_id', 'product_id'])
    op.drop_column('inventory_item', 'expiry_date')
    op.drop_column('inventory_item', 'opened_at')
    op.drop_column('inventory_item', 'status')
    
    # 3. ИЗМЕНЕНИЕ ТИПА С ЯВНЫМ УКАЗАНИЕМ (postgresql_using)
    op.alter_column('product', 'category',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.Enum('dairy', 'meat', 'fish', 'vegetables', 'fruits', 'groceries', 'drinks', 'frozen', 'sweets', 'other', name='product_category'),
               postgresql_using="category::product_category",  # <--- ВОТ ЭТА СТРОЧКА РЕШАЕТ ПРОБЛЕМУ
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Возвращаем тип колонки обратно в VARCHAR (тоже с явным указанием для надежности)
    op.alter_column('product', 'category',
               existing_type=sa.Enum('dairy', 'meat', 'fish', 'vegetables', 'fruits', 'groceries', 'drinks', 'frozen', 'sweets', 'other', name='product_category'),
               type_=sa.VARCHAR(length=50),
               postgresql_using="category::varchar",
               nullable=True)
    
    # 2. Возвращаем удаленные колонки и таблицы
    op.add_column('inventory_item', sa.Column('status', sa.VARCHAR(length=50), server_default=sa.text("'in_stock'::character varying"), autoincrement=False, nullable=False))
    op.add_column('inventory_item', sa.Column('opened_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('inventory_item', sa.Column('expiry_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_constraint('uq_inventory_household_product', 'inventory_item', type_='unique')
    op.create_index(op.f('ix_inventory_household_product'), 'inventory_item', ['household_id', 'product_id'], unique=False)
    op.create_table('inventory_event',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('inventory_item_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('event_type', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('quantity_change', sa.NUMERIC(precision=10, scale=3), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['inventory_item_id'], ['inventory_item.id'], name=op.f('inventory_event_inventory_item_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('inventory_event_user_id_fkey'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('inventory_event_pkey'))
    )
    op.create_index(op.f('ix_inventory_events_item'), 'inventory_event', ['inventory_item_id'], unique=False)
    
    # 3. Удаляем ENUM тип, когда он больше не используется
    op.execute("DROP TYPE product_category")