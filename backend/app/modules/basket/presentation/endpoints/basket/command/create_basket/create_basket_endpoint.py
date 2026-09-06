"""CreateBasket endpoint - FastAPI endpoint for basket creation."""

from typing import Any

from app.core.auth.rbac import require_user_or_higher
from app.core.repr.base import CQRSEndpointFactory
from app.modules.basket.application.features.basket.command.create_basket.create_basket_command import (
    CreateBasketCommand, CreateBasketResult)
from app.modules.basket.utils import get_endpoint_factory
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post(
    "/", response_model=CreateBasketResult, status_code=status.HTTP_201_CREATED
)
async def create_basket(
    request: CreateBasketCommand,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Allow user, manager, and admin roles (users should be able to create their own basket)
    _: Any = Depends(require_user_or_higher()),
) -> JSONResponse:
    """
    Create a new basket.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager, user roles)
    """
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=CreateBasketCommand,
        result_mapper=None,  # Will use default response mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, request)

    # Extract the result and return CreateBasketResult
    result = response.data  # This will be CreateBasketResult
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"id": str(result.id)},
        headers={"Location": f"/api/v1/basket/{result.id}"},
    )
