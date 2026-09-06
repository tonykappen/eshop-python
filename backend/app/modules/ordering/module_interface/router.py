"""Ordering module router registration."""

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.di.container import Container
from app.core.mediator.mediator import Mediator
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Import DI components
from app.modules.ordering.module_interface.di.orders import (
    get_ordering_container, get_ordering_message_bus,
    register_ordering_handlers_with_mediator, wire_ordering_dependencies)

# Queue name owned by the ordering module's basket-checkout consumer. Mirrors
# the MassTransit endpoint-per-consumer convention from the .NET reference.
_BASKET_CHECKOUT_QUEUE = "basket-checkout-queue"
_BASKET_EVENTS_EXCHANGE = "basket.events"

# Import order router
# Import health router
from app.modules.ordering.module_interface.health.health import \
    router as health_router
from app.modules.ordering.router.order_router import router as order_router


def register_ordering_module(container: Container, mediator: Mediator) -> APIRouter:
    """
    Register the ordering module with dependency injection and mediator.

    Args:
        container: Dependency injection container
        mediator: Mediator for CQRS operations

    Returns:
        FastAPI router for the ordering module
    """
    # Get ordering container and wire dependencies
    ordering_container = get_ordering_container()
    wire_ordering_dependencies(ordering_container)

    # Register handlers with mediator
    register_ordering_handlers_with_mediator(mediator)

    # Register integration event handlers
    subscribe_ordering_integration_event_handlers(mediator)

    # Create main router
    router = APIRouter(prefix="/api/v1", tags=["ordering"])

    # Include order router
    router.include_router(order_router)

    # Include health router
    router.include_router(health_router)

    return router


def subscribe_ordering_integration_event_handlers(_mediator: Mediator) -> None:
    """
    Subscribe ordering integration event handlers.

    This registers handlers for integration events from other modules (e.g., Basket).
    Note: Actual subscription to message bus happens in async startup callback.

    Args:
        mediator: Mediator instance for sending commands
    """
    logger.info(
        "Registered BasketCheckoutIntegrationEventHandler for ordering module "
        "(subscription to message bus will happen during startup)"
    )


def _coerce_basket_checkout_payload(event_data: dict[str, Any]) -> dict[str, Any]:
    """Coerce JSON-decoded basket checkout payload into model-friendly types.

    The basket outbox serialises ``customer_id`` and ``total_price`` as strings;
    Pydantic accepts them either way but we normalise here so the resulting
    model matches what local in-process handlers used to receive.
    """
    if not isinstance(event_data, dict):
        return event_data

    customer_id = event_data.get("customer_id")
    if isinstance(customer_id, str):
        try:
            event_data["customer_id"] = UUID(customer_id)
        except (ValueError, AttributeError):
            pass

    total_price = event_data.get("total_price")
    if isinstance(total_price, str):
        try:
            event_data["total_price"] = Decimal(total_price)
        except (ValueError, AttributeError):
            pass
    elif isinstance(total_price, (int, float)):
        event_data["total_price"] = Decimal(str(total_price))

    return event_data


async def subscribe_ordering_handlers_to_message_bus() -> None:
    """Subscribe ordering integration event handlers to RabbitMQ.

    Declares the durable ``basket-checkout-queue`` and binds it to the
    ``basket.events`` exchange with the routing key derived from
    ``BasketCheckoutIntegrationEvent.event_type``. This mirrors the .NET
    reference's MassTransit endpoint-per-consumer model so the queue is
    visible in the RabbitMQ Management UI even before any messages flow.
    """
    from app.core.mediator.fastapi_integration import get_mediator
    from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import \
        BasketCheckoutIntegrationEvent
    from app.modules.ordering.application.integration_event_handlers.basket.basket_checkout_integration_event_handler import \
        BasketCheckoutIntegrationEventHandler

    main_mediator = get_mediator()
    checkout_handler = BasketCheckoutIntegrationEventHandler(main_mediator)

    # Routing key matches the event_type produced by the basket outbox
    # publisher (IntegrationEvent._generate_event_type on the model default).
    routing_key = BasketCheckoutIntegrationEvent.model_fields["event_type"].default
    if not routing_key:
        # Fallback: instantiate-less generation by mimicking the algorithm.
        import re as _re

        class_name = BasketCheckoutIntegrationEvent.__name__
        if class_name.endswith("Event"):
            class_name = class_name[:-5]
        routing_key = _re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()

    async def _consume(event_data: Any) -> None:
        """Adapter: reconstruct typed event and invoke the existing handler."""
        try:
            payload = _coerce_basket_checkout_payload(event_data)
            event = BasketCheckoutIntegrationEvent(**payload)
            await checkout_handler.handle(event)
        except Exception:
            logger.exception(
                "Ordering basket-checkout consumer failed to handle message"
            )
            raise

    message_bus = get_ordering_message_bus()
    if hasattr(message_bus, "connect") and (
        not hasattr(message_bus, "_connection") or message_bus._connection is None
    ):
        await message_bus.connect()

    await message_bus.subscribe_to_exchange(
        exchange=_BASKET_EVENTS_EXCHANGE,
        routing_key=routing_key,
        queue_name=_BASKET_CHECKOUT_QUEUE,
        handler=_consume,
    )

    logger.info(
        "Subscribed BasketCheckoutIntegrationEventHandler to RabbitMQ "
        "(exchange=%s, routing_key=%s, queue=%s)",
        _BASKET_EVENTS_EXCHANGE,
        routing_key,
        _BASKET_CHECKOUT_QUEUE,
    )
