"""ShoppingCart ORM model for basket module."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.basket.infrastructure.persistence.orm.basket.base import Base


class ShoppingCartORM(Base):
    """ShoppingCart ORM model - matches .NET ShoppingCart entity configuration."""

    __tablename__ = "shopping_carts"
    __table_args__ = {"schema": "basket"}

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # User information
    user_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Version for optimistic concurrency
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    # Relationship to items
    items: Mapped[list["ShoppingCartItemORM"]] = relationship(
        "ShoppingCartItemORM",
        back_populates="shopping_cart",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ShoppingCartORM(id={self.id}, user_name='{self.user_name}')>"
