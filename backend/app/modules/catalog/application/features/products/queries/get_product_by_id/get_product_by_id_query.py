"""GetProductByIdQuery definition - matches .NET implementation."""

from typing import Any
from uuid import UUID

from app.core.contracts.cqrs import IQuery
from app.modules.catalog.application.public_interface.dto.product import \
    ProductDto
from pydantic import BaseModel, Field


class GetProductByIdQuery(IQuery[Any]):
    """Query to get a product by ID - matches .NET GetProductByIdQuery."""

    id: UUID = Field(..., description="Product ID to retrieve")


class GetProductByIdResult(BaseModel):
    """Result of getting a product by ID - matches .NET GetProductByIdResult."""

    product: ProductDto | None = Field(
        default=None,
        description="Product when found; None when not found",
    )
