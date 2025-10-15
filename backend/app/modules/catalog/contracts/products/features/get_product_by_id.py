"""Get product by ID feature contracts."""

from uuid import UUID

from pydantic import Field

from app.core.cqrs.base import IQuery
from app.modules.catalog.contracts.products.dtos import ProductDto


class GetProductByIdQuery(IQuery):
    """Query to get a product by its ID, matching .NET GetProductByIdQuery record."""

    id: UUID = Field(..., description="Product ID to retrieve")


class GetProductByIdResult(IQuery):
    """Result for GetProductByIdQuery, matching .NET GetProductByIdResult record."""

    product: ProductDto | None = Field(
        None, description="The retrieved product, None if not found"
    )
