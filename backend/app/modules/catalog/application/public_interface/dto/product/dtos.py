"""Product DTO for internal use within Catalog BC.

This DTO is used for:
- Query results (GetProductById, GetProducts, etc.)
- Internal service communication
- Mapping between domain models and public interfaces
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


class ProductDto(BaseModel):
    """
    Product DTO for internal Catalog BC use.

    This DTO represents a product in a format suitable for:
    - Query results
    - Internal service communication
    - Mapping to/from domain models and public DTOs
    """

    # Core identifiers
    id: UUID | str = Field(..., description="Product ID (UUID or string)")
    sku: str = Field(..., description="Product SKU (unique identifier)")

    # Product information
    name: str = Field(..., description="Product name")
    description: str | None = Field(None, description="Product description")
    category: list[str] = Field(default_factory=list, description="Product categories")

    # Media
    image_file: str | None = Field(None, description="Product image file path/URL")

    # Pricing information
    price: float = Field(..., description="Product price amount")
    currency: str = Field(default="USD", description="Product price currency (ISO 4217)")

    # Versioning
    version: int = Field(..., description="Product version (for optimistic concurrency)")

    # Timestamps (ISO 8601 strings)
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str | None = Field(None, description="Last update timestamp (ISO 8601)")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
        }
        # Allow population by field name or alias
        populate_by_name = True
