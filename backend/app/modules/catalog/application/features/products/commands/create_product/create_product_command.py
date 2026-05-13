"""CreateProductCommand definition - matches .NET implementation."""

from uuid import UUID

from pydantic import BaseModel, Field


class CreateProductCommand(BaseModel):
    """Command to create a new product - matches .NET CreateProductCommand."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    picture_url: str | None = Field(
        default=None, description="Product picture URL (optional)"
    )
    category: list[str] = Field(..., description="Product categories")


class CreateProductResult(BaseModel):
    """Result of creating a product - matches .NET CreateProductResult."""

    id: UUID = Field(..., description="Created product ID")
