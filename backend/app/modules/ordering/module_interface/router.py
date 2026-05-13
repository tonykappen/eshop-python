"""Ordering module router registration."""

import logging
import re

from fastapi import APIRouter

from app.core.di.container import Container
from app.core.mediator.mediator import Mediator

logger = logging.getLogger(__name__)

# Import DI components
from app.modules.ordering.module_interface.di.orders import (
    get_ordering_container,
    register_ordering_handlers_with_mediator,
    wire_ordering_dependencies,
)

# Import order router
from app.modules.ordering.router.order_router import router as order_router

# Import health router
from app.modules.ordering.module_interface.health.health import router as health_router


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


async def subscribe_ordering_handlers_to_message_bus() -> None:
    """
    Subscribe ordering integration event handlers to the shared message bus.
    
    This should be called during application startup after modules are registered.
    """
    from app.core.mediator.fastapi_integration import get_mediator
    from app.core.messaging.shared_message_bus import get_shared_message_bus
    from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import (
        BasketCheckoutIntegrationEvent,
    )
    from app.modules.ordering.application.integration_event_handlers.basket.basket_checkout_integration_event_handler import (
        BasketCheckoutIntegrationEventHandler,
    )

    # Get the main mediator (handlers need it to send commands)
    main_mediator = get_mediator()

    # Create and register the BasketCheckoutIntegrationEventHandler
    # This handler will receive BasketCheckoutIntegrationEvent events from the Basket module
    # and create orders
    checkout_handler = BasketCheckoutIntegrationEventHandler(main_mediator)

    # Topic must match BasketCheckoutIntegrationEvent.event_type (IntegrationEvent._generate_event_type)
    class_name = BasketCheckoutIntegrationEvent.__name__
    if class_name.endswith("Event"):
        class_name = class_name[:-5]
    event_type = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()

    message_bus = get_shared_message_bus()
    await message_bus.subscribe(event_type, checkout_handler)

    logger.info(
        f"Subscribed BasketCheckoutIntegrationEventHandler to message bus "
        f"for event type: '{event_type}'"
    )
