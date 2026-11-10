"""Fractional stock thresholds and indexed receipt candidate search.

Revision ID: b6c2d9e41001
Revises: afda5ea8a781
"""
from alembic import op
import sqlalchemy as sa

revision = "b6c2d9e41001"
down_revision = "afda5ea8a781"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("tracked_product", "minimum_quantity",
                    existing_type=sa.Integer(), type_=sa.Numeric(10, 3),
                    existing_nullable=False)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public")
    op.add_column("product", sa.Column(
        "search_text", sa.Text(),
        sa.Computed("lower(replace(name || ' ' || coalesce(brand, ''), 'ё', 'е'))", persisted=True),
        nullable=False,
    ))
    op.create_index("ix_product_search_trgm", "product", ["search_text"],
                    postgresql_using="gist", postgresql_ops={"search_text": "gist_trgm_ops"})
    op.create_check_constraint("ck_inventory_quantity_nonnegative", "inventory_item", "quantity >= 0")
    op.create_check_constraint("ck_tracked_minimum_positive", "tracked_product", "minimum_quantity > 0")
    op.create_check_constraint("ck_product_package_positive", "product", "package_quantity > 0")
    op.create_check_constraint("ck_product_name_not_blank", "product", "length(trim(name)) > 0")


def downgrade():
    # Do not silently round existing fractional thresholds on downgrade.
    op.execute("""DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM tracked_product WHERE minimum_quantity <> trunc(minimum_quantity)) THEN
            RAISE EXCEPTION 'Cannot downgrade: fractional minimum quantities exist';
        END IF;
    END $$""")
    op.drop_constraint("ck_product_name_not_blank", "product", type_="check")
    op.drop_constraint("ck_product_package_positive", "product", type_="check")
    op.drop_constraint("ck_tracked_minimum_positive", "tracked_product", type_="check")
    op.drop_constraint("ck_inventory_quantity_nonnegative", "inventory_item", type_="check")
    op.drop_index("ix_product_search_trgm", table_name="product")
    op.drop_column("product", "search_text")
    op.alter_column("tracked_product", "minimum_quantity",
                    existing_type=sa.Numeric(10, 3), type_=sa.Integer(),
                    postgresql_using="minimum_quantity::integer", existing_nullable=False)
