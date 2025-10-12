"""Initial migration for catalog module

Revision ID: 001
Revises:
Create Date: 2025-10-10 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create catalog schema and tables."""
    # Schema is created by env.py, so we only create tables here

    # Create products table
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("category", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("image_file", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_modified_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )

    # Create catalog_categories table
    op.create_table(
        "catalog_categories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_modified_by", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )

    # Create catalog_brands table
    op.create_table(
        "catalog_brands",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_modified_by", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )

    # Create catalog_items table
    op.create_table(
        "catalog_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("category_id", sa.String(length=36), nullable=True),
        sa.Column("brand_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_modified_by", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["brand_id"],
            ["catalog.catalog_brands.id"],
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["catalog.catalog_categories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )


def downgrade() -> None:
    """Drop catalog tables."""
    op.drop_table("catalog_items", schema="catalog")
    op.drop_table("catalog_brands", schema="catalog")
    op.drop_table("catalog_categories", schema="catalog")
    op.drop_table("products", schema="catalog")
