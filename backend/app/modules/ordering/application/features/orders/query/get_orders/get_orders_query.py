"""GetOrdersQuery definition - matches .NET implementation."""

from pydantic import BaseModel, Field

from app.core.pagination.models import PaginatedResult
from app.modules.ordering.application.dtos.order_dto import OrderDto


class PaginationRequest(BaseModel):
    """Pagination request matching .NET PaginationRequest record."""

    page_index: int = Field(default=0, ge=0, description="Page index (0-based)")
    page_size: int = Field(default=10, ge=1, description="Page size")


class GetOrdersQuery(BaseModel):
    """Query to get orders - matches .NET GetOrdersQuery."""

    pagination_request: PaginationRequest = Field(
        ..., description="Pagination request"
    )


class GetOrdersResult(BaseModel):
    """Result of getting orders - matches .NET GetOrdersResult."""

    orders: PaginatedResult[OrderDto] = Field(..., description="Paginated orders")
