"""AddItemIntoBasket endpoint - FastAPI endpoint for adding item to basket."""

from typing import Any

from app.core.auth.rbac import require_user_or_higher
from app.core.repr.base import CQRSEndpointFactory
from app.modules.basket.application.dtos.shopping_cart_dto import \
    ShoppingCartItemDto
from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_command import (
    AddItemIntoBasketCommand, AddItemIntoBasketResult)
from app.modules.basket.utils import get_endpoint_factory
from fastapi import APIRouter, Depends, Path, Request, Response, status
from pydantic import BaseModel

router = APIRouter()


class AddItemIntoBasketRequest(BaseModel):
    """Request model for adding item to basket - matches Postman collection format."""

    shopping_cart_item: ShoppingCartItemDto


@router.post(
    "/{user_name}/items",
    response_model=AddItemIntoBasketResult,
    status_code=status.HTTP_201_CREATED,
)
async def add_item_into_basket(
    user_name: str = Path(..., description="User name"),
    request: AddItemIntoBasketRequest = ...,
    http_request: Request = ...,
    http_response: Response = ...,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Allow user, manager, and admin roles (users should be able to add items to their cart)
    _: Any = Depends(require_user_or_higher()),
) -> AddItemIntoBasketResult:
    """
    Add item into basket.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager, user roles)
    """
    # Create command with user_name from path and shopping_cart_item from body
    command = AddItemIntoBasketCommand(
        user_name=user_name, shopping_cart_item=request.shopping_cart_item
    )

    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=AddItemIntoBasketCommand,
        result_mapper=None,
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return AddItemIntoBasketResult
    result = response.data  # This will be AddItemIntoBasketResult

    # Set Location header for 201 Created response
    http_response.headers["Location"] = f"/api/v1/basket/{user_name}"

    return result
