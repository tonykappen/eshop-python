"""Initial catalog schema

Revision ID: 0001
Revises:
Create Date: 2025-01-15 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial catalog schema."""
    # Create catalog schema
    op.execute("CREATE SCHEMA IF NOT EXISTS catalog")

    # Create products table
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("image_file", sa.String(length=500), nullable=False),
        sa.Column("price_amount", sa.String(length=20), nullable=False),
        sa.Column("price_currency", sa.String(length=3), nullable=False),
        sa.Column("categories", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )

    # Create unique index on SKU
    op.create_index(
        "ix_products_sku", "products", ["sku"], unique=True, schema="catalog"
    )

    # Create index on name
    op.create_index("ix_products_name", "products", ["name"], schema="catalog")

    # Create index on categories
    op.create_index(
        "ix_products_categories",
        "products",
        ["categories"],
        postgresql_using="gin",
        schema="catalog",
    )

    # Create categories table
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )

    # Create unique index on category name
    op.create_index(
        "ix_categories_name", "categories", ["name"], unique=True, schema="catalog"
    )

    # Create index on parent_id
    op.create_index(
        "ix_categories_parent_id", "categories", ["parent_id"], schema="catalog"
    )

    # Create inventory_items table
    op.create_table(
        "inventory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False),
        sa.Column("reorder_threshold", sa.Integer(), nullable=False),
        sa.Column("max_stock_threshold", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )

    # Create unique index on product_id
    op.create_index(
        "ix_inventory_items_product_id",
        "inventory_items",
        ["product_id"],
        unique=True,
        schema="catalog",
    )

    # Create outbox table for reliable messaging
    op.create_table(
        "outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("event_data", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )

    # Create index on status for outbox processing
    op.create_index("ix_outbox_status", "outbox", ["status"], schema="catalog")

    # Create index on created_at for outbox processing
    op.create_index("ix_outbox_created_at", "outbox", ["created_at"], schema="catalog")


def downgrade() -> None:
    """Drop catalog schema."""
    # Drop tables in reverse order
    op.drop_table("outbox", schema="catalog")
    op.drop_table("inventory_items", schema="catalog")
    op.drop_table("categories", schema="catalog")
    op.drop_table("products", schema="catalog")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS catalog")
