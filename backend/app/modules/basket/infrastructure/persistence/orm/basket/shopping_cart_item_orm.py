"""ShoppingCartItem ORM model for basket module."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.basket.infrastructure.persistence.orm.basket.base import Base


class ShoppingCartItemORM(Base):
    """ShoppingCartItem ORM model - matches .NET ShoppingCartItem entity configuration."""

    __tablename__ = "shopping_cart_items"
    __table_args__ = {"schema": "basket"}

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Foreign key to shopping cart
    shopping_cart_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("basket.shopping_carts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Product information
    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=False
    )

    # Item details
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship to shopping cart
    shopping_cart: Mapped["ShoppingCartORM"] = relationship(
        "ShoppingCartORM", back_populates="items"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ShoppingCartItemORM(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"
