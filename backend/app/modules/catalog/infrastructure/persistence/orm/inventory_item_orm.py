"""Inventory item ORM model for catalog module."""

from datetime import datetime
from uuid import UUID, uuid4

from app.modules.catalog.infrastructure.persistence.orm.base import Base
from sqlalchemy import DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column


class InventoryItemORM(Base):
    """Inventory item ORM model."""

    __tablename__ = "inventory_items"
    __table_args__ = {"schema": "catalog"}

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Product reference
    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=False, unique=True
    )

    # Inventory information
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_stock_threshold: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1000
    )

    # Audit fields
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<InventoryItemORM(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "quantity": self.quantity,
            "reserved_quantity": self.reserved_quantity,
            "reorder_threshold": self.reorder_threshold,
            "max_stock_threshold": self.max_stock_threshold,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "is_deleted": self.is_deleted,
        }
