"""GetProductsByCategory endpoint - FastAPI endpoint for getting products filtered by category."""

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.core.auth.rbac import require_query_access
from app.core.repr.base import CQRSEndpointFactory, PaginatedResultToResponseMapper
from app.modules.catalog.application.features.products.queries.get_products_by_category.query import (
    GetProductsByCategoryQuery,
    GetProductsByCategoryResult,
)
from app.modules.catalog.utils import get_endpoint_factory

router = APIRouter()


@router.get("/", response_model=GetProductsByCategoryResult)
async def get_products_by_category(
    http_request: Request,
    category: str = Query(..., description="Category name to filter products by"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Query access required (admin, manager, user)
    _: Any = Depends(require_query_access()),
) -> GetProductsByCategoryResult:
    """
    Get products filtered by category with pagination.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response (with pagination)
    RBAC: Requires query access (admin, manager, user roles)
    """
    # Create the query
    query = GetProductsByCategoryQuery(
        category=category,
        page=page,
        page_size=page_size,
    )

    # Create query endpoint with custom pagination mapper
    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetProductsByCategoryQuery,
        result_mapper=PaginatedResultToResponseMapper[GetProductsByCategoryResult](),
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, query)

    return response  # type: ignore
