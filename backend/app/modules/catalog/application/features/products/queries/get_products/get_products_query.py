"""GetProductsQuery definition - matches .NET implementation."""

from uuid import UUID

from pydantic import BaseModel

from app.core.pagination.models import PaginatedResult
from app.modules.catalog.application.public_interface.dto.product import ProductDto


class GetProductsQuery(BaseModel):
    """Query to get products with pagination - matches .NET GetProductsQuery."""

    page: int = 1
    page_size: int = 10
    category_id: UUID | None = None
    search_term: str | None = None


class GetProductsResult(PaginatedResult[ProductDto]):
    """Result of getting products - matches .NET GetProductsResult."""

    pass
