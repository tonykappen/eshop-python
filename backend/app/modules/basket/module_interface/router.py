"""Basket module wiring - router, DI, mediator registration."""

import logging

from app.core.di.container import Container
from app.core.mediator.mediator import Mediator
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Import commands and queries

# Import DI components
from app.modules.basket.module_interface.di.basket import (
    get_basket_container, register_basket_handlers_with_mediator,
    wire_basket_dependencies, wire_basket_dependencies_to_fastapi)
# Import health router
from app.modules.basket.module_interface.health.health import \
    router as health_router
# Import basket router
from app.modules.basket.router.basket_router import router as basket_router


def register_basket_module(container: Container, mediator: Mediator) -> APIRouter:
    """
    Register the basket module with dependency injection and mediator.

    Args:
        container: Dependency injection container
        mediator: Mediator for CQRS operations

    Returns:
        FastAPI router for the basket module
    """
    # Get basket container and wire dependencies
    basket_container = get_basket_container()
    wire_basket_dependencies(basket_container)

    # Register handlers with mediator
    # Note: Handlers will be created per-request via FastAPI DI through CQRSEndpointFactory
    # The actual handler registration happens in register_basket_handlers_with_mediator
    # which sets up the handler registry. Handlers are resolved dynamically when
    # commands/queries are sent through the mediator.
    register_basket_handlers_with_mediator(mediator)

    # Register integration event handlers
    # This subscribes the basket module to integration events from other modules
    subscribe_basket_integration_event_handlers(mediator)

    # Create main router
    router = APIRouter(prefix="/api/v1", tags=["basket"])

    # Include basket router
    router.include_router(basket_router)

    # Include health router
    router.include_router(health_router)

    return router


def register_basket_module_with_fastapi(
    app, container: Container, mediator: Mediator
) -> APIRouter:
    """
    Register the basket module with FastAPI app and dependency injection.

    Args:
        app: FastAPI application instance
        container: Dependency injection container
        mediator: Mediator for CQRS operations

    Returns:
        FastAPI router for the basket module
    """
    basket_container = get_basket_container()
    wire_basket_dependencies_to_fastapi(app, container, mediator)

    register_basket_handlers_with_mediator(mediator)

    subscribe_basket_integration_event_handlers(mediator)

    router = APIRouter(prefix="/api/v1", tags=["basket"])
    router.include_router(basket_router)
    router.include_router(health_router)

    return router


def subscribe_basket_integration_event_handlers(_mediator: Mediator) -> None:
    """
    Prepare basket integration event handlers.

    Wires the basket module for integration events from other modules (e.g., Catalog).
    This creates the handler instance used when events are dispatched; actual subscription
    to the shared in-memory message bus happens in subscribe_basket_handlers_to_message_bus()
    during application startup.

    Args:
        mediator: Mediator instance for sending commands
    """
    from app.core.mediator.fastapi_integration import get_mediator
    from app.modules.basket.application.integration_event_handlers.products.product_price_changed_integration_event_handler import \
        ProductPriceChangedIntegrationEventHandler

    main_mediator = get_mediator()

    _handler = ProductPriceChangedIntegrationEventHandler(main_mediator)

    logger.info("Created ProductPriceChangedIntegrationEventHandler for basket module")


async def subscribe_basket_handlers_to_message_bus() -> None:
    """
    Subscribe basket integration event handlers to the shared message bus.

    This should be called during application startup after modules are registered.
    """
    from app.core.mediator.fastapi_integration import get_mediator
    from app.core.messaging.shared_message_bus import get_shared_message_bus
    from app.modules.basket.application.integration_event_handlers.products.product_price_changed_integration_event_handler import \
        ProductPriceChangedIntegrationEventHandler
    from app.modules.catalog.contracts.products.integration_events.v1.product_price_changed_integration_event import \
        ProductPriceChangedIntegrationEventV1

    main_mediator = get_mediator()

    price_changed_handler = ProductPriceChangedIntegrationEventHandler(main_mediator)

    event_type = ProductPriceChangedIntegrationEventV1.model_fields[
        "event_type"
    ].default

    message_bus = get_shared_message_bus()
    await message_bus.subscribe(event_type, price_changed_handler)

    logger.info(
        "Subscribed ProductPriceChangedIntegrationEventHandler to message bus "
        "for event type: '%s'",
        event_type,
    )
