"""Product ORM model for catalog module."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID  # noqa: N811
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.catalog.infrastructure.persistence.models.base import Base


class ProductORM(Base):
    """Product ORM model."""

    __tablename__ = "products"
    __table_args__ = {"schema": "catalog"}

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Product information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_file: Mapped[str] = mapped_column(String(500), nullable=False)

    # Price information
    price_amount: Mapped[Decimal] = mapped_column(String(20), nullable=False)
    price_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD"
    )

    # Categories
    categories: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
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
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True
    )
    deletion_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ProductORM(id={self.id}, name='{self.name}', sku='{self.sku}')>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "sku": self.sku,
            "description": self.description,
            "image_file": self.image_file,
            "price_amount": float(self.price_amount),
            "price_currency": self.price_currency,
            "categories": self.categories,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
            "deletion_reason": self.deletion_reason,
        }
