"""Order router - groups all order endpoints."""

from app.modules.ordering.presentation.endpoints.orders.command.create_order import \
    router as create_order_router
from app.modules.ordering.presentation.endpoints.orders.command.delete_order import \
    router as delete_order_router
from app.modules.ordering.presentation.endpoints.orders.query.get_order_by_id import \
    router as get_order_by_id_router
from app.modules.ordering.presentation.endpoints.orders.query.get_orders import \
    router as get_orders_router
from fastapi import APIRouter

router = APIRouter(prefix="/orders", tags=["orders"])

# Include command endpoints
router.include_router(create_order_router)
router.include_router(delete_order_router)

# Include query endpoints
router.include_router(get_order_by_id_router)
router.include_router(get_orders_router)
