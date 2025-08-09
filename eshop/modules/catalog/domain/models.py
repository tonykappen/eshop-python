"""Product domain models."""

from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from eshop.core.domain.entity import Aggregate
from eshop.modules.catalog.domain.events import (
    ProductCreatedEvent,
    ProductPriceChangedEvent,
)


class Product(Aggregate):
    """Product aggregate following .NET Product class structure."""

    name: str = Field(..., description="Product name")
    category: list[str] = Field(default_factory=list, description="Product categories")
    description: str = Field(..., description="Product description")
    image_file: str = Field(..., description="Product image file path")
    price: Decimal = Field(..., description="Product price", gt=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate product name is not empty."""
        if not v or not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip()

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError("Product price must be positive")
        return v

    @classmethod
    def create(
        cls,
        product_id: UUID,
        name: str,
        category: list[str],
        description: str,
        image_file: str,
        price: Decimal,
    ) -> "Product":
        """Create a new product, matching .NET Product.Create static method."""
        # Validation happens in Pydantic validators
        product = cls(
            id=product_id,
            name=name,
            category=category,
            description=description,
            image_file=image_file,
            price=price,
        )

        # Add domain event
        product.add_domain_event(ProductCreatedEvent(product=product))

        return product

    def update(
        self,
        name: str,
        category: list[str],
        description: str,
        image_file: str,
        price: Decimal,
    ) -> None:
        """Update product details, matching .NET Product.Update method."""
        # Store old price for comparison
        old_price = self.price

        # Update fields
        self.name = name
        self.category = category
        self.description = description
        self.image_file = image_file
        self.price = price

        # If price changed, add domain event
        if old_price != price:
            self.add_domain_event(ProductPriceChangedEvent(product=self))
