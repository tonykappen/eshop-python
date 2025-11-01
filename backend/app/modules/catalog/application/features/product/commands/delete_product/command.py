"""DeleteProductCommand definition - matches .NET implementation."""

from uuid import UUID
from pydantic import BaseModel


class DeleteProductCommand(BaseModel):
    """Command to delete a product - matches .NET DeleteProductCommand."""

    product_id: UUID
    deleted_by: UUID | None = None
    deletion_reason: str | None = None


class DeleteProductResult(BaseModel):
    """Result of deleting a product - matches .NET DeleteProductResult."""

    is_success: bool
