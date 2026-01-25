"""Product Public DTO for cross-BC consumption.

This DTO is designed for inter-bounded context communication.
It provides a stable, versioned contract that other bounded contexts
can depend on without tight coupling to the Catalog BC's internal structure.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.modules.catalog.application.public_interface.dto.product import ProductDto


class ProductPublicDto(BaseModel):
    """
    Public DTO for cross-bounded context consumption.

    This DTO is designed to be:
    - Stable: Changes should be versioned
    - Minimal: Only essential fields for cross-BC communication
    - Serializable: Easy to serialize/deserialize for messaging
    - Backward compatible: Changes should not break consumers

    Used for:
    - Integration events (e.g., ProductCreatedIntegrationEvent)
    - Cross-BC queries (e.g., Basket BC querying product info)
    - Event sourcing snapshots
    - API contracts between BCs
    """

    # Core identifiers
    id: UUID = Field(..., description="Product ID (UUID)")
    sku: str = Field(..., description="Product SKU (unique identifier)")

    # Essential product information
    name: str = Field(..., description="Product name")
    description: str | None = Field(None, description="Product description")

    # Pricing information
    price_amount: Decimal = Field(..., description="Product price amount")
    price_currency: str = Field(
        default="USD", description="Product price currency (ISO 4217)"
    )

    # Categorization
    categories: list[str] = Field(
        default_factory=list, description="Product categories"
    )

    # Media
    image_file: str | None = Field(None, description="Product image file path/URL")

    # Status and versioning
    is_active: bool = Field(
        default=True, description="Whether the product is active/available"
    )
    version: int = Field(
        ..., description="Product version (for optimistic concurrency)"
    )

    # Timestamps (ISO 8601 strings for cross-BC compatibility)
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str | None = Field(
        None, description="Last update timestamp (ISO 8601)"
    )

    # Optional metadata for cross-BC context
    metadata: dict | None = Field(
        None,
        description="Optional metadata for cross-BC communication (e.g., source BC, event ID)",
    )

    class Config:
        """Pydantic configuration for cross-BC compatibility."""

        json_encoders = {
            UUID: str,
            Decimal: lambda v: str(v),  # Keep as string for precision
        }
        # Use enum values for serialization
        use_enum_values = True
        # Allow population by field name or alias
        populate_by_name = True

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "id": str(self.id),
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "price_amount": str(self.price_amount),
            "price_currency": self.price_currency,
            "categories": self.categories,
            "image_file": self.image_file,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata or {},
        }

    @property
    def price(self) -> str:
        """
        Get formatted price string.

        Returns:
            Formatted price string (e.g., "99.99 USD")
        """
        return f"{self.price_amount} {self.price_currency}"

    @classmethod
    def from_product_dto(cls, product_dto: ProductDto) -> ProductPublicDto:
        """
        Create ProductPublicDto from internal ProductDto.

        Args:
            product_dto: Internal ProductDto from dtos.py

        Returns:
            ProductPublicDto instance
        """
        # Type checking only - import here to avoid circular dependency


        return cls(
            id=product_dto.id,
            sku=product_dto.sku,
            name=product_dto.name,
            description=product_dto.description,
            price_amount=Decimal(str(product_dto.price)),
            price_currency=product_dto.currency,
            categories=product_dto.category,
            image_file=product_dto.image_file,
            is_active=True,  # Default to active unless explicitly set
            version=product_dto.version,
            created_at=product_dto.created_at,
            updated_at=product_dto.updated_at,
        )


# Type alias for convenience
ProductPublicDTO = ProductPublicDto
