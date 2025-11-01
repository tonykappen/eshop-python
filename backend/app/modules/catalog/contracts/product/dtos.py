"""Product DTOs for public contracts."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductDto(BaseModel):
    """Product Data Transfer Object for public API."""

    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    sku: str = Field(..., min_length=1, max_length=100, description="Product SKU")
    category: list[str] = Field(
        ..., min_length=1, description="Product categories (at least one required)"
    )
    description: str = Field(
        ..., min_length=1, max_length=5000, description="Product description"
    )
    image_file: str | None = Field(
        default=None,
        max_length=500,
        description="Product image file path (optional)",
    )
    price: float = Field(..., ge=0, description="Product price (must be >= 0)")
    currency: str = Field(
        default="USD", min_length=3, max_length=3, description="Product currency (ISO 4217)"
    )
    version: int = Field(..., ge=0, description="Product version (must be >= 0)")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            Decimal: float,
        }


class ProductSummaryDto(BaseModel):
    """Product summary DTO for list views."""

    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    sku: str = Field(..., min_length=1, max_length=100, description="Product SKU")
    category: list[str] = Field(
        ..., min_length=1, description="Product categories (at least one required)"
    )
    price: float = Field(..., ge=0, description="Product price (must be >= 0)")
    currency: str = Field(
        default="USD", min_length=3, max_length=3, description="Product currency (ISO 4217)"
    )
    image_file: str | None = Field(
        default=None,
        max_length=500,
        description="Product image file path (optional)",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            Decimal: float,
        }


class ProductSearchDto(BaseModel):
    """Product search DTO."""

    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    sku: str = Field(..., min_length=1, max_length=100, description="Product SKU")
    category: list[str] = Field(
        ..., min_length=1, description="Product categories (at least one required)"
    )
    description: str = Field(
        ..., min_length=1, max_length=5000, description="Product description"
    )
    price: float = Field(..., ge=0, description="Product price (must be >= 0)")
    currency: str = Field(
        default="USD", min_length=3, max_length=3, description="Product currency (ISO 4217)"
    )
    image_file: str | None = Field(
        default=None,
        max_length=500,
        description="Product image file path (optional)",
    )
    relevance_score: float | None = Field(
        None, ge=0, le=1, description="Search relevance score (0.0 to 1.0)"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            Decimal: float,
        }
