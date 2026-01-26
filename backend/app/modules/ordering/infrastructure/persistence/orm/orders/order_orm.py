"""Order ORM model for ordering module - matches .NET OrderConfiguration exactly."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.ordering.infrastructure.persistence.orm.orders.base import Base


class OrderORM(Base):
    """
    Order ORM model - matches .NET OrderConfiguration exactly.

    Complex properties (Address, Payment) are embedded as columns matching .NET ComplexProperty.
    """

    __tablename__ = "orders"
    __table_args__ = (
        # Unique index on order_name matching .NET HasIndex().IsUnique()
        Index("ix_orders_order_name", "order_name", unique=True),
        {"schema": "ordering"},
    )

    # Primary key - matching .NET HasKey(e => e.Id)
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Customer ID - matching .NET Property(o => o.CustomerId)
    customer_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=False
    )

    # Order name - matching .NET Property(e => e.OrderName).IsRequired().HasMaxLength(100)
    order_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Shipping Address - ComplexProperty matching .NET configuration
    # FirstName: HasMaxLength(50), IsRequired()
    shipping_address_first_name: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    # LastName: HasMaxLength(50), IsRequired()
    shipping_address_last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    # EmailAddress: HasMaxLength(50), optional
    shipping_address_email_address: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    # AddressLine: HasMaxLength(180), IsRequired()
    shipping_address_address_line: Mapped[str] = mapped_column(
        String(180), nullable=False
    )
    # Country: HasMaxLength(50), optional
    shipping_address_country: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    # State: HasMaxLength(50), optional
    shipping_address_state: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    # ZipCode: HasMaxLength(5), IsRequired()
    shipping_address_zip_code: Mapped[str] = mapped_column(String(5), nullable=False)

    # Billing Address - ComplexProperty matching .NET configuration (same as shipping)
    billing_address_first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    billing_address_last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    billing_address_email_address: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    billing_address_address_line: Mapped[str] = mapped_column(
        String(180), nullable=False
    )
    billing_address_country: Mapped[str | None] = mapped_column(String(50), nullable=True)
    billing_address_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    billing_address_zip_code: Mapped[str] = mapped_column(String(5), nullable=False)

    # Payment - ComplexProperty matching .NET configuration
    # CardName: HasMaxLength(50), optional
    payment_card_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # CardNumber: HasMaxLength(24), IsRequired()
    payment_card_number: Mapped[str] = mapped_column(String(24), nullable=False)
    # Expiration: HasMaxLength(10), optional
    payment_expiration: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # CVV: HasMaxLength(3), optional
    payment_cvv: Mapped[str | None] = mapped_column(String(3), nullable=True)
    # PaymentMethod: integer, required
    payment_payment_method: Mapped[int] = mapped_column(Integer, nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Version for optimistic concurrency
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    # Relationship to items - matching .NET HasMany(s => s.Items).WithOne().HasForeignKey(si => si.OrderId)
    items: Mapped[list["OrderItemORM"]] = relationship(
        "OrderItemORM",
        back_populates="order",
        cascade="all, delete-orphan",
        foreign_keys="OrderItemORM.order_id",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<OrderORM(id={self.id}, order_name='{self.order_name}')>"
