"""UpdateItemPriceInBasket endpoint - FastAPI endpoint for updating item price in basket."""

from typing import Any
from uuid import UUID

from app.core.auth.rbac import require_command_access
from app.core.repr.base import CQRSEndpointFactory
from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_command import (
    UpdateItemPriceInBasketCommand, UpdateItemPriceInBasketResult)
from app.modules.basket.utils import get_endpoint_factory
from fastapi import APIRouter, Body, Depends, Path, Request

router = APIRouter()


@router.put(
    "/{user_name}/items/{product_id}/price",
    response_model=UpdateItemPriceInBasketResult,
)
async def update_item_price_in_basket(
    http_request: Request,
    user_name: str = Path(..., description="User name"),
    product_id: UUID = Path(..., description="Product ID"),
    price: float = Body(..., description="New price"),
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager)
    _: Any = Depends(require_command_access()),
) -> UpdateItemPriceInBasketResult:
    """
    Update item price in basket.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles)
    """
    from decimal import Decimal

    # Create command from path and body parameters
    command = UpdateItemPriceInBasketCommand(
        product_id=product_id, price=Decimal(str(price))
    )

    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=UpdateItemPriceInBasketCommand,
        result_mapper=None,
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return UpdateItemPriceInBasketResult
    result = response.data  # This will be UpdateItemPriceInBasketResult
    return UpdateItemPriceInBasketResult(is_success=result.is_success)
