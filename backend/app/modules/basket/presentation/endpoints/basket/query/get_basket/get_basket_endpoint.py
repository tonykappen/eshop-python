"""GetBasket endpoint - FastAPI endpoint for getting basket."""

from typing import Any

from app.core.auth.rbac import require_query_access
from app.core.repr.base import CQRSEndpointFactory
from app.modules.basket.application.features.basket.query.get_basket.get_basket_query import (
    GetBasketQuery, GetBasketResult)
from app.modules.basket.utils import get_endpoint_factory
from fastapi import APIRouter, Depends, Path, Request

router = APIRouter()


@router.get("/{user_name}", response_model=GetBasketResult)
async def get_basket(
    user_name: str = Path(..., description="User name"),
    http_request: Request = ...,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Query access required (admin, manager, user)
    _: Any = Depends(require_query_access()),
) -> GetBasketResult:
    """
    Get basket by user name.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response
    RBAC: Requires query access (admin, manager, user roles)
    """
    # Create query endpoint using factory
    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetBasketQuery,
        result_mapper=None,  # Will use default response mapper
    )

    # Create the query with user name
    query = GetBasketQuery(user_name=user_name)

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, query)

    # Extract the result and return GetBasketResult
    result = response.data  # This will be GetBasketResult
    return GetBasketResult(shopping_cart=result.shopping_cart)
