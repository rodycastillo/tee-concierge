"""catalog and faq

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("material", sa.String(120), nullable=False, server_default=""),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("image_url", sa.String(500)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_products_category_active", "products", ["category_id", "active"])
    op.create_table(
        "variants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False, unique=True),
        sa.Column("size", sa.String(8), nullable=False),
        sa.Column("color", sa.String(40), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("product_id", "size", "color", name="uq_variant_product_size_color"),
        sa.CheckConstraint("stock >= 0", name="ck_variant_stock_non_negative"),
    )
    op.create_index("ix_variants_product_id", "variants", ["product_id"])
    op.create_table(
        "faq_entries",
        sa.Column("topic", sa.String(40), primary_key=True),
        sa.Column("body", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("faq_entries")
    op.drop_index("ix_variants_product_id", table_name="variants")
    op.drop_table("variants")
    op.drop_index("ix_products_category_active", table_name="products")
    op.drop_table("products")
    op.drop_table("categories")
