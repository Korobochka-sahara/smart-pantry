"""refactor composite keys and receipts

Revision ID: 8c1b7d4a92ef
Revises: 25132b8228e8
Create Date: 2026-09-15

Changes:
- household_member: remove surrogate id, use (household_id, user_id) PK
- inventory_item: remove surrogate id, use (household_id, product_id) PK
- tracked_product: remove surrogate id, use (household_id, product_id) PK
- product: barcode becomes unique when not NULL
- receipt: remove total_amount
- receipt_item: remove total_price
- add index for household_member.user_id
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c1b7d4a92ef"
down_revision: Union[str, Sequence[str], None] = "25132b8228e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # household_member: id -> composite PK
    op.drop_constraint(
        "uq_household_member",
        "household_member",
        type_="unique",
    )
    op.drop_constraint(
        "household_member_pkey",
        "household_member",
        type_="primary",
    )
    op.drop_column("household_member", "id")
    op.create_primary_key(
        "household_member_pkey",
        "household_member",
        ["household_id", "user_id"],
    )
    op.create_index(
        "ix_household_member_user_id",
        "household_member",
        ["user_id"],
        unique=False,
    )

    # inventory_item: id -> composite PK
    op.drop_constraint(
        "uq_inventory_household_product",
        "inventory_item",
        type_="unique",
    )
    op.drop_constraint(
        "inventory_item_pkey",
        "inventory_item",
        type_="primary",
    )
    op.drop_column("inventory_item", "id")
    op.create_primary_key(
        "inventory_item_pkey",
        "inventory_item",
        ["household_id", "product_id"],
    )

    # tracked_product: id -> composite PK
    op.drop_constraint(
        "uq_tracked_product",
        "tracked_product",
        type_="unique",
    )
    op.drop_constraint(
        "tracked_product_pkey",
        "tracked_product",
        type_="primary",
    )
    op.drop_column("tracked_product", "id")
    op.create_primary_key(
        "tracked_product_pkey",
        "tracked_product",
        ["household_id", "product_id"],
    )

    # Product barcode: keep NULLs allowed, but non-NULL values must be unique.
    op.drop_index(
        "ix_product_barcode",
        table_name="product",
    )
    op.create_unique_constraint(
        "uq_product_barcode",
        "product",
        ["barcode"],
    )

    # Receipt no longer stores the total amount.
    op.drop_column("receipt", "total_amount")

    # ReceiptItem no longer stores calculated total_price.
    op.drop_column("receipt_item", "total_price")


def downgrade() -> None:
    # Restore receipt_item.total_price. Existing historical values cannot be
    # reconstructed from the new schema, so use 0 as a placeholder.
    op.add_column(
        "receipt_item",
        sa.Column(
            "total_price",
            sa.Numeric(precision=10, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    # Restore receipt.total_amount. Existing historical values cannot be
    # reconstructed, so use 0 as a placeholder.
    op.add_column(
        "receipt",
        sa.Column(
            "total_amount",
            sa.Numeric(precision=10, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    # Product barcode: unique constraint -> ordinary index.
    op.drop_constraint(
        "uq_product_barcode",
        "product",
        type_="unique",
    )
    op.create_index(
        "ix_product_barcode",
        "product",
        ["barcode"],
        unique=False,
    )

    # tracked_product: composite PK -> id + unique constraint
    op.drop_constraint(
        "tracked_product_pkey",
        "tracked_product",
        type_="primary",
    )
    op.add_column(
        "tracked_product",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=True),
    )
    op.execute(
        sa.text(
            "CREATE SEQUENCE IF NOT EXISTS tracked_product_id_seq"
        )
    )
    op.execute(
        sa.text(
            "UPDATE tracked_product "
            "SET id = nextval('tracked_product_id_seq') "
            "WHERE id IS NULL"
        )
    )
    op.alter_column(
        "tracked_product",
        "id",
        nullable=False,
        server_default=sa.text("nextval('tracked_product_id_seq')"),
    )
    op.create_primary_key(
        "tracked_product_pkey",
        "tracked_product",
        ["id"],
    )
    op.create_unique_constraint(
        "uq_tracked_product",
        "tracked_product",
        ["household_id", "product_id"],
    )

    # inventory_item: composite PK -> id + unique constraint
    op.drop_constraint(
        "inventory_item_pkey",
        "inventory_item",
        type_="primary",
    )
    op.add_column(
        "inventory_item",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=True),
    )
    op.execute(
        sa.text(
            "CREATE SEQUENCE IF NOT EXISTS inventory_item_id_seq"
        )
    )
    op.execute(
        sa.text(
            "UPDATE inventory_item "
            "SET id = nextval('inventory_item_id_seq') "
            "WHERE id IS NULL"
        )
    )
    op.alter_column(
        "inventory_item",
        "id",
        nullable=False,
        server_default=sa.text("nextval('inventory_item_id_seq')"),
    )
    op.create_primary_key(
        "inventory_item_pkey",
        "inventory_item",
        ["id"],
    )
    op.create_unique_constraint(
        "uq_inventory_household_product",
        "inventory_item",
        ["household_id", "product_id"],
    )

    # household_member: composite PK -> id + unique constraint
    op.drop_index(
        "ix_household_member_user_id",
        table_name="household_member",
    )
    op.drop_constraint(
        "household_member_pkey",
        "household_member",
        type_="primary",
    )
    op.add_column(
        "household_member",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=True),
    )
    op.execute(
        sa.text(
            "CREATE SEQUENCE IF NOT EXISTS household_member_id_seq"
        )
    )
    op.execute(
        sa.text(
            "UPDATE household_member "
            "SET id = nextval('household_member_id_seq') "
            "WHERE id IS NULL"
        )
    )
    op.alter_column(
        "household_member",
        "id",
        nullable=False,
        server_default=sa.text("nextval('household_member_id_seq')"),
    )
    op.create_primary_key(
        "household_member_pkey",
        "household_member",
        ["id"],
    )
    op.create_unique_constraint(
        "uq_household_member",
        "household_member",
        ["household_id", "user_id"],
    )
