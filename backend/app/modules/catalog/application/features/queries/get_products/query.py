"""GetProductsQuery definition - matches .NET implementation."""

from uuid import UUID
from typing import Optional
from pydantic import BaseModel

from app.modules.catalog.contracts.products.dtos import ProductDto
from app.core.pagination.models import PaginatedResult


class GetProductsQuery(BaseModel):
    """Query to get products with pagination - matches .NET GetProductsQuery."""

    page: int = 1
    page_size: int = 10
    category_id: Optional[UUID] = None
    search_term: Optional[str] = None


class GetProductsResult(PaginatedResult[ProductDto]):
    """Result of getting products - matches .NET GetProductsResult."""

    pass
