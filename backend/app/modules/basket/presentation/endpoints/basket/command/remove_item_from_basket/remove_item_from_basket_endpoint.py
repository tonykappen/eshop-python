"""RemoveItemFromBasket endpoint - FastAPI endpoint for removing item from basket."""

from typing import Any
from uuid import UUID

from app.core.auth.rbac import require_user_or_higher
from app.core.repr.base import CQRSEndpointFactory
from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_command import (
    RemoveItemFromBasketCommand, RemoveItemFromBasketResult)
from app.modules.basket.utils import get_endpoint_factory
from fastapi import APIRouter, Depends, Path, Request

router = APIRouter()


@router.delete(
    "/{user_name}/items/{product_id}", response_model=RemoveItemFromBasketResult
)
async def remove_item_from_basket(
    user_name: str = Path(..., description="User name"),
    product_id: UUID = Path(..., description="Product ID to remove"),
    http_request: Request | None = None,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Allow user, manager, and admin roles (users should be able to remove items from their cart)
    _: Any = Depends(require_user_or_higher()),
) -> RemoveItemFromBasketResult:
    """
    Remove item from basket.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager, user roles)
    """
    # Create command from path parameters
    command = RemoveItemFromBasketCommand(user_name=user_name, product_id=product_id)

    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=RemoveItemFromBasketCommand,
        result_mapper=None,
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return RemoveItemFromBasketResult
    result = response.data  # This will be RemoveItemFromBasketResult
    return RemoveItemFromBasketResult(id=result.id)
