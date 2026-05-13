"""Add deletion metadata fields to products

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-31 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add deletion metadata fields to products table."""
    # Add deletion metadata columns
    op.add_column(
        "products",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        schema="catalog",
    )
    op.add_column(
        "products",
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        schema="catalog",
    )
    op.add_column(
        "products",
        sa.Column("deletion_reason", sa.String(length=500), nullable=True),
        schema="catalog",
    )

    # Create index on deleted_at for faster queries of deleted products
    op.create_index(
        "ix_products_deleted_at", "products", ["deleted_at"], schema="catalog"
    )


def downgrade() -> None:
    """Remove deletion metadata fields from products table."""
    # Drop index
    op.drop_index("ix_products_deleted_at", table_name="products", schema="catalog")

    # Drop columns
    op.drop_column("products", "deletion_reason", schema="catalog")
    op.drop_column("products", "deleted_by", schema="catalog")
    op.drop_column("products", "deleted_at", schema="catalog")
