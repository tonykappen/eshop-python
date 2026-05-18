"""OrderItem ORM model for ordering module - matches .NET OrderItemConfiguration exactly."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.modules.ordering.infrastructure.persistence.orm.orders.base import \
    Base
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class OrderItemORM(Base):
    """
    OrderItem ORM model - matches .NET OrderItemConfiguration exactly.
    """

    __tablename__ = "order_items"
    __table_args__ = {"schema": "ordering"}

    # Primary key - matching .NET HasKey(e => e.Id)
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Foreign key to order - matching .NET HasForeignKey(si => si.OrderId)
    order_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("ordering.orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Product ID - matching .NET Property(oi => oi.ProductId).IsRequired()
    product_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)

    # Quantity - matching .NET Property(oi => oi.Quantity).IsRequired()
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Price - matching .NET Property(oi => oi.Price).IsRequired()
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship to order
    order: Mapped["OrderORM"] = relationship("OrderORM", back_populates="items")

    def __repr__(self) -> str:
        """String representation."""
        return f"<OrderItemORM(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"
