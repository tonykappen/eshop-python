"""Ordering application module."""

from app.modules.ordering.application.dtos import (
    AddressDto,
    OrderDto,
    OrderItemDto,
    PaymentDto,
)
from app.modules.ordering.application.features.orders.command.create_order import (
    CreateOrderCommand,
    CreateOrderHandler,
    CreateOrderResult,
)
from app.modules.ordering.application.features.orders.command.delete_order import (
    DeleteOrderCommand,
    DeleteOrderHandler,
    DeleteOrderResult,
)
from app.modules.ordering.application.features.orders.query.get_order_by_id import (
    GetOrderByIdHandler,
    GetOrderByIdQuery,
    GetOrderByIdResult,
)
from app.modules.ordering.application.features.orders.query.get_orders import (
    GetOrdersHandler,
    GetOrdersQuery,
    GetOrdersResult,
)

__all__ = [
    "OrderDto",
    "OrderItemDto",
    "AddressDto",
    "PaymentDto",
    "CreateOrderCommand",
    "CreateOrderResult",
    "CreateOrderHandler",
    "DeleteOrderCommand",
    "DeleteOrderResult",
    "DeleteOrderHandler",
    "GetOrderByIdQuery",
    "GetOrderByIdResult",
    "GetOrderByIdHandler",
    "GetOrdersQuery",
    "GetOrdersResult",
    "GetOrdersHandler",
]
