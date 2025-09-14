"""SQLAlchemy ORM models for the Catalog module."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import Base


class ProductORM(Base):
    """ORM model for products - matches .NET Product entity."""

    __tablename__ = "products"
    __table_args__ = {"schema": "catalog"}

    # Primary key
    id: Mapped[str] = mapped_column(UUID, primary_key=True)

    # Basic properties
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    image_file: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)

    # Audit fields
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_modified_by: Mapped[str | None] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<ProductORM(id={self.id}, name={self.name}, price={self.price})>"


class CatalogItemORM(Base):
    """ORM model for catalog items."""

    __tablename__ = "catalog_items"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Basic properties
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(nullable=False, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Foreign keys
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("catalog_categories.id"), nullable=True
    )
    brand_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("catalog_brands.id"), nullable=True
    )

    # Audit fields
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_modified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    category: Mapped[Optional["CatalogCategoryORM"]] = relationship(
        "CatalogCategoryORM", back_populates="items"
    )
    brand: Mapped[Optional["CatalogBrandORM"]] = relationship(
        "CatalogBrandORM", back_populates="items"
    )

    def __repr__(self) -> str:
        return f"<CatalogItemORM(id={self.id}, name={self.name}, price={self.price})>"


class CatalogCategoryORM(Base):
    """ORM model for catalog categories."""

    __tablename__ = "catalog_categories"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Basic properties
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit fields
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_modified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    items: Mapped[list[CatalogItemORM]] = relationship(
        "CatalogItemORM", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<CatalogCategoryORM(id={self.id}, name={self.name})>"


class CatalogBrandORM(Base):
    """ORM model for catalog brands."""

    __tablename__ = "catalog_brands"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Basic properties
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Audit fields
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_modified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    items: Mapped[list[CatalogItemORM]] = relationship(
        "CatalogItemORM", back_populates="brand"
    )

    def __repr__(self) -> str:
        return f"<CatalogBrandORM(id={self.id}, name={self.name})>"
