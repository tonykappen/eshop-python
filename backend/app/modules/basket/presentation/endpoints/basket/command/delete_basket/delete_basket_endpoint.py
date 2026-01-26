"""DeleteBasket endpoint - FastAPI endpoint for deleting basket."""

from typing import Any

from fastapi import APIRouter, Depends, Path, Request

from app.core.auth.rbac import require_command_access
from app.core.repr.base import CQRSEndpointFactory
from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_command import (
    DeleteBasketCommand,
    DeleteBasketResult,
)
from app.modules.basket.utils import get_endpoint_factory

router = APIRouter()


@router.delete("/{user_name}", response_model=DeleteBasketResult)
async def delete_basket(
    user_name: str = Path(..., description="User name"),
    http_request: Request = ...,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager, user)
    _: Any = Depends(require_command_access()),
) -> DeleteBasketResult:
    """
    Delete basket.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager, user roles)
    """
    # Create command from path parameters
    command = DeleteBasketCommand(user_name=user_name)

    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=DeleteBasketCommand,
        result_mapper=None,
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return DeleteBasketResult
    result = response.data  # This will be DeleteBasketResult
    return DeleteBasketResult(is_success=result.is_success)
