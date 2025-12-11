"""GetProductByIdQuery definition - matches .NET implementation."""

from uuid import UUID
from pydantic import BaseModel

from app.modules.catalog.application.public_interface.dto.product import ProductDto


class GetProductByIdQuery(BaseModel):
    """Query to get a product by ID - matches .NET GetProductByIdQuery."""

    id: UUID


class GetProductByIdResult(BaseModel):
    """Result of getting a product by ID - matches .NET GetProductByIdResult."""

    product: ProductDto
