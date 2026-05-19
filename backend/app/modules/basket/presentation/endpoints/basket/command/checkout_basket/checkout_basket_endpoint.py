"""CheckoutBasket endpoint - FastAPI endpoint for basket checkout."""

from typing import Any

from app.core.auth.rbac import require_user_or_higher
from app.core.repr.base import CQRSEndpointFactory
from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_command import (
    CheckoutBasketCommand, CheckoutBasketResult)
from app.modules.basket.utils import get_endpoint_factory
from fastapi import APIRouter, Body, Depends, Path, Request

router = APIRouter()


@router.post("/{user_name}/checkout", response_model=CheckoutBasketResult)
async def checkout_basket(
    http_request: Request,
    user_name: str = Path(..., description="User name"),
    body: CheckoutBasketCommand = Body(...),
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Allow user, manager, and admin roles (users should be able to checkout their own basket)
    _: Any = Depends(require_user_or_higher()),
) -> CheckoutBasketResult:
    """
    Checkout basket.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager, user roles)
    """
    # Update command with user_name from path
    command = CheckoutBasketCommand(basket_checkout=body.basket_checkout)
    command.basket_checkout.user_name = user_name

    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=CheckoutBasketCommand,
        result_mapper=None,
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return CheckoutBasketResult
    result = response.data  # This will be CheckoutBasketResult
    return CheckoutBasketResult(is_success=result.is_success)
