"""DeleteOrder endpoint - FastAPI endpoint for order deletion."""

from typing import Any
from uuid import UUID

from app.core.auth.rbac import require_command_access
from app.core.repr.base import CQRSEndpointFactory
from app.modules.ordering.application.features.orders.command.delete_order.delete_order_command import (
    DeleteOrderCommand, DeleteOrderResult)
from app.modules.ordering.utils import get_endpoint_factory
from fastapi import APIRouter, Depends, Path, Request, status

router = APIRouter()


@router.delete(
    "/{order_id}", response_model=DeleteOrderResult, status_code=status.HTTP_200_OK
)
async def delete_order(
    order_id: UUID = Path(..., description="Order ID"),
    http_request: Request = ...,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager)
    _: Any = Depends(require_command_access()),
) -> DeleteOrderResult:
    """
    Delete an order - matches .NET DeleteOrderEndpoint.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles)
    """
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=DeleteOrderCommand,
        result_mapper=None,  # Will use default response mapper
    )

    # Create the command with order ID
    command = DeleteOrderCommand(order_id=order_id)

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return DeleteOrderResult
    result = response.data  # This will be DeleteOrderResult
    return DeleteOrderResult(is_success=result.is_success)
