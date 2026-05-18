"""GetProductByIdQuery definition - matches .NET implementation."""

from uuid import UUID

from app.modules.catalog.application.public_interface.dto.product import \
    ProductDto
from pydantic import BaseModel


class GetProductByIdQuery(BaseModel):
    """Query to get a product by ID - matches .NET GetProductByIdQuery."""

    id: UUID


class GetProductByIdResult(BaseModel):
    """Result of getting a product by ID - matches .NET GetProductByIdResult."""

    product: ProductDto
