"""CreateOrder endpoint - FastAPI endpoint for order creation."""

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.core.auth.rbac import require_command_access
from app.core.repr.base import CQRSEndpointFactory
from app.modules.ordering.application.features.orders.command.create_order.create_order_command import (
    CreateOrderCommand,
    CreateOrderResult,
)
from app.modules.ordering.utils import get_endpoint_factory

router = APIRouter()


@router.post(
    "/",
    response_model=CreateOrderResult,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    request: CreateOrderCommand,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager)
    _: Any = Depends(require_command_access()),
) -> CreateOrderResult:
    """
    Create a new order - matches .NET CreateOrderEndpoint.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles)
    """
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=CreateOrderCommand,
        result_mapper=None,  # Will use default response mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, request)

    # Extract the result and return CreateOrderResult
    result = response.data  # This will be CreateOrderResult
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"id": str(result.id)},
        headers={"Location": f"/api/v1/orders/{result.id}"},
    )
