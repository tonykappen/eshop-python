"""Product DTOs for public contracts."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductDto(BaseModel):
    """Product Data Transfer Object for public API."""

    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    sku: str = Field(..., description="Product SKU")
    category: list[str] = Field(..., description="Product categories")
    description: str = Field(..., description="Product description")
    image_file: str | None = Field(
        default=None, description="Product image file path (optional)"
    )
    price: float = Field(..., description="Product price")
    currency: str = Field(default="USD", description="Product currency")
    version: int = Field(..., description="Product version")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            Decimal: float,
        }


class ProductSummaryDto(BaseModel):
    """Product summary DTO for list views."""

    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    sku: str = Field(..., description="Product SKU")
    category: list[str] = Field(..., description="Product categories")
    price: float = Field(..., description="Product price")
    currency: str = Field(default="USD", description="Product currency")
    image_file: str | None = Field(
        default=None, description="Product image file path (optional)"
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
    name: str = Field(..., description="Product name")
    sku: str = Field(..., description="Product SKU")
    category: list[str] = Field(..., description="Product categories")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    currency: str = Field(default="USD", description="Product currency")
    image_file: str | None = Field(
        default=None, description="Product image file path (optional)"
    )
    relevance_score: float | None = Field(None, description="Search relevance score")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            Decimal: float,
        }
