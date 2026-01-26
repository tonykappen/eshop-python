"""Initial basket schema

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
    """Create initial basket schema."""
    # Create basket schema
    op.execute("CREATE SCHEMA IF NOT EXISTS basket")

    # Create shopping_carts table
    op.create_table(
        "shopping_carts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="basket",
    )

    # Create unique index on user_name
    op.create_index(
        "ix_shopping_carts_user_name",
        "shopping_carts",
        ["user_name"],
        unique=True,
        schema="basket",
    )

    # Create shopping_cart_items table
    op.create_table(
        "shopping_cart_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopping_cart_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=50), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["shopping_cart_id"],
            ["basket.shopping_carts.id"],
            ondelete="CASCADE",
        ),
        schema="basket",
    )

    # Create index on shopping_cart_id
    op.create_index(
        "ix_shopping_cart_items_shopping_cart_id",
        "shopping_cart_items",
        ["shopping_cart_id"],
        schema="basket",
    )

    # Create index on product_id for price updates
    op.create_index(
        "ix_shopping_cart_items_product_id",
        "shopping_cart_items",
        ["product_id"],
        schema="basket",
    )

    # Create outbox table for reliable messaging
    op.create_table(
        "outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("event_data", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column("trace_context", postgresql.JSONB(), nullable=True),
        sa.Column("baggage", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="basket",
    )

    # Create index on status for outbox processing
    op.create_index("ix_outbox_status", "outbox", ["status"], schema="basket")

    # Create index on created_at for outbox processing
    op.create_index("ix_outbox_created_at", "outbox", ["created_at"], schema="basket")


def downgrade() -> None:
    """Drop basket schema."""
    # Drop tables in reverse order
    op.drop_table("outbox", schema="basket")
    op.drop_table("shopping_cart_items", schema="basket")
    op.drop_table("shopping_carts", schema="basket")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS basket")
