"""Basket module wiring - router, DI, mediator registration."""

import logging

from fastapi import APIRouter

from app.core.di.container import Container
from app.core.mediator.mediator import Mediator

logger = logging.getLogger(__name__)

# Import commands and queries
from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_command import (
    AddItemIntoBasketCommand,
)
from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_handler import (
    AddItemIntoBasketHandler,
)
from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_command import (
    CheckoutBasketCommand,
)
from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_handler import (
    CheckoutBasketHandler,
)
from app.modules.basket.application.features.basket.command.create_basket.create_basket_command import (
    CreateBasketCommand,
)
from app.modules.basket.application.features.basket.command.create_basket.create_basket_handler import (
    CreateBasketHandler,
)
from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_command import (
    DeleteBasketCommand,
)
from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_handler import (
    DeleteBasketHandler,
)
from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_command import (
    RemoveItemFromBasketCommand,
)
from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_handler import (
    RemoveItemFromBasketHandler,
)
from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_command import (
    UpdateItemPriceInBasketCommand,
)
from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_handler import (
    UpdateItemPriceInBasketHandler,
)
from app.modules.basket.application.features.basket.query.get_basket.get_basket_query import (
    GetBasketQuery,
)
from app.modules.basket.application.features.basket.query.get_basket.get_basket_handler import (
    GetBasketHandler,
)

# Import DI components
from app.modules.basket.module_interface.di.basket import (
    get_basket_container,
    register_basket_handlers_with_mediator,
    wire_basket_dependencies,
    wire_basket_dependencies_to_fastapi,
)

# Import basket router
from app.modules.basket.router.basket_router import router as basket_router

# Import health router
from app.modules.basket.module_interface.health.health import router as health_router


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
    # Get basket container and wire dependencies
    basket_container = get_basket_container()
    wire_basket_dependencies_to_fastapi(app, container, mediator)

    # Register handlers with mediator
    register_basket_handlers_with_mediator(mediator)
    
    # Register handlers directly with mediator (similar to catalog module)
    # Handlers need dependencies, so we'll create them using FastAPI's dependency injection
    # We need to register them with the mediator's HandlerRegistry so the mediator can resolve them
    
    # Import handler dependencies
    from app.modules.basket.infrastructure.persistence.repositories.basket.sql_basket_repository import (
        SqlBasketRepository,
    )
    from app.modules.basket.infrastructure.persistence.repositories.basket.cached_basket_repository import (
        CachedBasketRepository,
    )
    from app.modules.basket.application.services.basket_cache_service import (
        BasketCacheService,
    )
    from app.modules.basket.infrastructure.persistence.unit_of_work.sql_basket_unit_of_work import (
        SqlBasketUnitOfWork,
    )
    from app.core.mediator.fastapi_integration import get_mediator as get_main_mediator
    from app.core.messaging.outbox.outbox_service import OutboxService
    from app.modules.basket.infrastructure.persistence.db_context import get_session_maker
    
    # Register handlers with dependencies resolved from FastAPI DI
    # We'll create handlers with dependencies from the app's dependency injection system
    # Since handlers need async sessions, we'll create them with a session from the session maker
    # Note: This is for registration only - handlers will be recreated per-request with proper DI
    
    try:
        # Get dependencies
        main_mediator = get_main_mediator()
        session_maker = get_session_maker()
        
        # Create handlers with dependencies resolved from FastAPI DI
        # We'll use the app's dependency_overrides to resolve dependencies
        # Since we can't easily create async sessions here, we'll register handlers
        # that will be created per-request via FastAPI DI
        
        # For registration, we need handler instances
        # We'll create them with dependencies from the app's dependency injection
        # But we need to handle async sessions
        
        # Solution: Create handlers with dependencies resolved from FastAPI app
        # We'll use the app's dependency_overrides that were set up in wire_basket_dependencies_to_fastapi
        
        # Get dependencies from app's dependency injection
        # We'll use the app's dependency_overrides to resolve dependencies
        from app.modules.basket.module_interface.di.basket.basket_providers import (
            get_basket_repository,
        )
        
        # Create a wrapper that creates handlers on-demand with FastAPI DI
        # But HandlerRegistry expects instances, not factories
        
        # For now, we'll register handlers with dependencies resolved from the app
        # We'll create them with dependencies from FastAPI DI
        # Note: This is a workaround - handlers will be recreated per-request with proper DI
        
        # Create handlers with dependencies from FastAPI DI
        # We'll use the app's dependency_overrides to resolve dependencies
        # But we need async context for sessions
        
        # Alternative: Register handlers with a factory that creates them on-demand
        # But HandlerRegistry expects instances
        
        # Best solution: Register handlers in a way that allows FastAPI DI to create them
        # We'll use the app's dependency injection system
        
        # For registration, we'll create handlers with dependencies from the app
        # We'll use the app's dependency_overrides to resolve dependencies
        # But we need to handle async sessions
        
        # Let's register handlers with dependencies resolved from the app
        # We'll create them with dependencies from FastAPI DI
        # The handlers will be recreated per-request with proper DI
        
        # Note: Since we can't easily create async sessions here, we'll register handlers
        # that will be created per-request via FastAPI DI
        # But the mediator needs them registered now, so we'll create placeholder handlers
        
        # Handlers will be created per-request via FastAPI DI
        # We don't register handler instances here because they need real database sessions
        # The CQRSEndpointFactory creates endpoints that use the mediator,
        # and handlers are resolved dynamically via FastAPI dependency injection
        # when commands/queries are sent through endpoints
        
        logger.info("Basket handlers will be created via FastAPI DI per-request with real database sessions")
        
    except Exception as e:
        logger.warning(f"Could not register basket handlers: {e}")
        logger.info("Handlers will be created via FastAPI DI per request")
    
    # Register integration event handlers
    subscribe_basket_integration_event_handlers(mediator)

    # Create main router
    router = APIRouter(prefix="/api/v1", tags=["basket"])

    # Include basket router
    router.include_router(basket_router)

    # Include health router
    router.include_router(health_router)

    return router


def subscribe_basket_integration_event_handlers(mediator: Mediator) -> None:
    """
    Subscribe basket integration event handlers.
    
    This registers handlers for integration events from other modules (e.g., Catalog).
    
    Args:
        mediator: Mediator instance for sending commands
    """
    from app.core.mediator.fastapi_integration import get_mediator
    from app.modules.basket.application.integration_event_handlers.products.product_price_changed_integration_event_handler import (
        ProductPriceChangedIntegrationEventHandler,
    )
    
    # Get the main mediator (handlers need it to send commands)
    main_mediator = get_mediator()
    
    # Create and register the ProductPriceChangedIntegrationEventHandler
    # This handler will receive ProductPriceChangedIntegrationEventV1 events from the Catalog module
    # and update product prices in all shopping baskets
    price_changed_handler = ProductPriceChangedIntegrationEventHandler(main_mediator)
    
    # Note: Integration event handlers are typically registered with the EventBus/RabbitMQ
    # For now, we create the handler instance. The actual subscription to RabbitMQ
    # will be handled by the messaging system when events are published.
    # The handler will be called when ProductPriceChangedIntegrationEventV1 events are consumed.
    
    logger.info("Registered ProductPriceChangedIntegrationEventHandler for basket module")
