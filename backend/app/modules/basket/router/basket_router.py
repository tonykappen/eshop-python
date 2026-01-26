"""Basket router - groups all basket endpoints."""

from fastapi import APIRouter

# Import all basket endpoint routers
from app.modules.basket.presentation.endpoints.basket.command.add_item_into_basket.add_item_into_basket_endpoint import (
    router as add_item_into_basket_router,
)
from app.modules.basket.presentation.endpoints.basket.command.checkout_basket.checkout_basket_endpoint import (
    router as checkout_basket_router,
)
from app.modules.basket.presentation.endpoints.basket.command.create_basket.create_basket_endpoint import (
    router as create_basket_router,
)
from app.modules.basket.presentation.endpoints.basket.command.delete_basket.delete_basket_endpoint import (
    router as delete_basket_router,
)
from app.modules.basket.presentation.endpoints.basket.command.remove_item_from_basket.remove_item_from_basket_endpoint import (
    router as remove_item_from_basket_router,
)
from app.modules.basket.presentation.endpoints.basket.command.update_item_price_in_basket.update_item_price_in_basket_endpoint import (
    router as update_item_price_in_basket_router,
)
from app.modules.basket.presentation.endpoints.basket.query.get_basket.get_basket_endpoint import (
    router as get_basket_router,
)

# Create the main basket router
router = APIRouter(prefix="/basket", tags=["basket"])

# Include all basket endpoint routers
router.include_router(create_basket_router)
router.include_router(get_basket_router)
router.include_router(add_item_into_basket_router)
router.include_router(remove_item_from_basket_router)
router.include_router(update_item_price_in_basket_router)
router.include_router(delete_basket_router)
router.include_router(checkout_basket_router)
