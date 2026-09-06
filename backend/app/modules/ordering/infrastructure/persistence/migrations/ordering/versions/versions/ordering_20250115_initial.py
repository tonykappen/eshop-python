"""Initial ordering schema

Revision ID: f26d684fe7af
Revises: 
Create Date: 2025-01-15 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f26d684fe7af"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial ordering schema."""
    # Create ordering schema
    op.execute("CREATE SCHEMA IF NOT EXISTS ordering")

    # Create orders table - matching .NET OrderConfiguration
    op.create_table(
        "orders",
        # Primary key - matching .NET HasKey(e => e.Id)
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        # Customer ID - matching .NET Property(o => o.CustomerId)
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Order name - matching .NET Property(e => e.OrderName).IsRequired().HasMaxLength(100)
        sa.Column("order_name", sa.String(length=100), nullable=False),
        # Shipping Address - ComplexProperty matching .NET configuration
        sa.Column("shipping_address_first_name", sa.String(length=50), nullable=False),
        sa.Column("shipping_address_last_name", sa.String(length=50), nullable=False),
        sa.Column(
            "shipping_address_email_address", sa.String(length=50), nullable=True
        ),
        sa.Column(
            "shipping_address_address_line", sa.String(length=180), nullable=False
        ),
        sa.Column("shipping_address_country", sa.String(length=50), nullable=True),
        sa.Column("shipping_address_state", sa.String(length=50), nullable=True),
        sa.Column("shipping_address_zip_code", sa.String(length=5), nullable=False),
        # Billing Address - ComplexProperty matching .NET configuration
        sa.Column("billing_address_first_name", sa.String(length=50), nullable=False),
        sa.Column("billing_address_last_name", sa.String(length=50), nullable=False),
        sa.Column("billing_address_email_address", sa.String(length=50), nullable=True),
        sa.Column(
            "billing_address_address_line", sa.String(length=180), nullable=False
        ),
        sa.Column("billing_address_country", sa.String(length=50), nullable=True),
        sa.Column("billing_address_state", sa.String(length=50), nullable=True),
        sa.Column("billing_address_zip_code", sa.String(length=5), nullable=False),
        # Payment - ComplexProperty matching .NET configuration
        sa.Column("payment_card_name", sa.String(length=50), nullable=True),
        sa.Column("payment_card_number", sa.String(length=24), nullable=False),
        sa.Column("payment_expiration", sa.String(length=10), nullable=True),
        sa.Column("payment_cvv", sa.String(length=3), nullable=True),
        sa.Column("payment_payment_method", sa.Integer(), nullable=False),
        # Audit fields
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Version for optimistic concurrency
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        schema="ordering",
    )

    # Create unique index on order_name - matching .NET HasIndex(e => e.OrderName).IsUnique()
    op.create_index(
        "ix_orders_order_name",
        "orders",
        ["order_name"],
        unique=True,
        schema="ordering",
    )

    # Create order_items table - matching .NET OrderItemConfiguration
    op.create_table(
        "order_items",
        # Primary key - matching .NET HasKey(e => e.Id)
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        # Foreign key to order - matching .NET HasForeignKey(si => si.OrderId)
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        # Product ID - matching .NET Property(oi => oi.ProductId).IsRequired()
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Quantity - matching .NET Property(oi => oi.Quantity).IsRequired()
        sa.Column("quantity", sa.Integer(), nullable=False),
        # Price - matching .NET Property(oi => oi.Price).IsRequired()
        sa.Column("price", sa.Numeric(precision=18, scale=2), nullable=False),
        # Audit fields
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["ordering.orders.id"],
            ondelete="CASCADE",
        ),
        schema="ordering",
    )


def downgrade() -> None:
    """Drop ordering schema."""
    # Drop tables in reverse order
    op.drop_table("order_items", schema="ordering")
    op.drop_index("ix_orders_order_name", table_name="orders", schema="ordering")
    op.drop_table("orders", schema="ordering")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS ordering")
