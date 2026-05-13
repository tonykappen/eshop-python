"""GetProducts endpoint - FastAPI endpoint for getting products with pagination."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.core.auth.rbac import require_query_access
from app.core.repr.base import CQRSEndpointFactory, PaginatedResultToResponseMapper
from app.modules.catalog.utils import get_endpoint_factory

from .get_products_query import GetProductsQuery, GetProductsResult

router = APIRouter()


@router.get("/", response_model=GetProductsResult)
async def get_products(
    http_request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: UUID | None = Query(None),
    search_term: str | None = Query(None),
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Query access required (admin, manager, user)
    _: Any = Depends(require_query_access()),
) -> GetProductsResult:
    """
    Get products with pagination and filtering.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response (with pagination)
    RBAC: Requires query access (admin, manager, user roles)
    """
    # Create the query
    query = GetProductsQuery(
        page=page, page_size=page_size, category_id=category_id, search_term=search_term
    )

    # Create query endpoint with custom pagination mapper
    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetProductsQuery,
        result_mapper=PaginatedResultToResponseMapper[GetProductsResult](),
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, query)

    return response  # type: ignore
