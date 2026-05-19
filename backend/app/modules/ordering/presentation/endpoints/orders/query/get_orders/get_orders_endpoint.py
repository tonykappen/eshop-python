"""GetOrders endpoint - FastAPI endpoint for getting orders with pagination."""

from typing import Any

from app.core.auth.rbac import require_query_access
from app.core.repr.base import CQRSEndpointFactory
from app.modules.ordering.application.features.orders.query.get_orders.get_orders_query import (
    GetOrdersQuery, GetOrdersResult, PaginationRequest)
from app.modules.ordering.utils import get_endpoint_factory
from fastapi import APIRouter, Depends, Query, Request

router = APIRouter()


@router.get("/", response_model=GetOrdersResult)
async def get_orders(
    page_index: int = Query(0, ge=0, description="Page index (0-based)"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    http_request: Request | None = None,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Query access required (admin, manager, user)
    _: Any = Depends(require_query_access()),
) -> GetOrdersResult:
    """
    Get orders with pagination - matches .NET GetOrdersEndpoint.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response
    RBAC: Requires query access (admin, manager, user roles)
    """
    # Create query endpoint using factory
    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetOrdersQuery,
        result_mapper=None,  # Will use default response mapper
    )

    # Create the query with pagination
    query = GetOrdersQuery(
        pagination_request=PaginationRequest(page_index=page_index, page_size=page_size)
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, query)

    # Extract the result and return GetOrdersResult
    result = response.data  # This will be GetOrdersResult
    return GetOrdersResult(orders=result.orders)
