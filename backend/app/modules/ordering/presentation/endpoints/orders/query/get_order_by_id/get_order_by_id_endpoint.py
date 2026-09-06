"""GetOrderById endpoint - FastAPI endpoint for getting order by ID."""

from typing import Any
from uuid import UUID

from app.core.auth.rbac import require_query_access
from app.core.repr.base import CQRSEndpointFactory
from app.modules.ordering.application.features.orders.query.get_order_by_id.get_order_by_id_query import (
    GetOrderByIdQuery, GetOrderByIdResult)
from app.modules.ordering.utils import get_endpoint_factory
from fastapi import APIRouter, Depends, Path, Request

router = APIRouter()


@router.get("/{order_id}", response_model=GetOrderByIdResult)
async def get_order_by_id(
    http_request: Request,
    order_id: UUID = Path(..., description="Order ID"),
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Query access required (admin, manager, user)
    _: Any = Depends(require_query_access()),
) -> GetOrderByIdResult:
    """
    Get order by ID - matches .NET GetOrderByIdEndpoint.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response
    RBAC: Requires query access (admin, manager, user roles)
    """
    # Create query endpoint using factory
    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetOrderByIdQuery,
        result_mapper=None,  # Will use default response mapper
    )

    # Create the query with order ID
    query = GetOrderByIdQuery(id=order_id)

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, query)

    # Extract the result and return GetOrderByIdResult
    result = response.data  # This will be GetOrderByIdResult
    return GetOrderByIdResult(order=result.order)
