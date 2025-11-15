"""UpdateProductCommand definition - matches .NET implementation."""

from uuid import UUID
from pydantic import BaseModel


class UpdateProductCommand(BaseModel):
    """Command to update an existing product - matches .NET UpdateProductCommand."""

    id: UUID | None = None  # Optional in request body, will be set from URL path
    name: str
    description: str
    price: float
    picture_url: str | None = None  # Optional
    category: list[str]


class UpdateProductResult(BaseModel):
    """Result of updating a product - matches .NET UpdateProductResult."""

    is_success: bool
