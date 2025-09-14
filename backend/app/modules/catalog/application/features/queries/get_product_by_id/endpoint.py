"""GetProductById endpoint - FastAPI endpoint for getting product by ID."""

from fastapi import APIRouter, Depends, Request
from typing import Any
from uuid import UUID

from app.core.repr.base import CQRSEndpointFactory, get_endpoint_factory
from app.core.auth.rbac import require_query_access
from .query import GetProductByIdQuery, GetProductByIdResult

router = APIRouter()


@router.get("/{product_id}", response_model=GetProductByIdResult)
async def get_product_by_id(
    product_id: UUID,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Query access required (admin, manager, user)
    _: Any = Depends(require_query_access()),
) -> GetProductByIdResult:
    """
    Get a product by ID.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response
    RBAC: Requires query access (admin, manager, user roles)
    """
    # Create query endpoint using factory
    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetProductByIdQuery,
        result_mapper=None,  # Will use default response mapper
    )

    # Create the query with product ID
    query = GetProductByIdQuery(id=product_id)

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, query)

    # Extract the result and return GetProductByIdResult
    result = response.data  # This will be GetProductByIdResult
    return GetProductByIdResult(product=result.product)
