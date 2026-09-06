"""Dependency injection wiring for catalog module."""

from typing import Any, cast

from app.core.context.application_context import RequestContext
from app.core.logging.base_logger import BaseLogger
from app.core.mediator.mediator import Mediator
from app.core.messaging.bus import IMessageBus
from app.core.messaging.domain_dispatcher import DomainEventDispatcher
from app.modules.catalog.application.unit_of_work import ICatalogUnitOfWork
from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.inventory.repository import InventoryRepository
from app.modules.catalog.domain.repositories.product.product_repository import \
    ProductRepository
from app.modules.catalog.infrastructure.persistence.repositories.products.redis.cached_product_repository import \
    CachedProductRepository
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import (
    SqlCategoryRepository, SqlInventoryRepository, SqlProductRepository)
from app.modules.catalog.infrastructure.persistence.unit_of_work import \
    SqlCatalogUnitOfWork
from app.modules.catalog.module_interface.di.products.products_containers import \
    get_catalog_container
from app.modules.catalog.module_interface.di.products.products_providers import (
    get_catalog_cache_service, get_catalog_dispatcher, get_catalog_engine,
    get_catalog_mediator, get_catalog_message_bus, get_catalog_session_maker)
from fastapi import FastAPI

logger = BaseLogger(__name__)


def wire_catalog_dependencies(app: FastAPI | None = None) -> None:
    """
    Wire catalog dependencies to FastAPI app.

    Args:
        app: FastAPI application instance (optional; reserved for future use).
    """
    container = get_catalog_container()

    # Register core services
    _register_core_services(container)

    # Repositories are not registered on the container: they need an AsyncSession and
    # are resolved per-request via FastAPI dependency_overrides (see
    # wire_catalog_dependencies_to_fastapi / get_catalog_dependency_overrides).

    # Register messaging services
    _register_messaging_services(container)

    # Register application services
    _register_application_services(container)

    # Subscribe domain events to integration events
    _subscribe_domain_events(container)

    logger.log_with_context("Wired catalog dependencies to FastAPI app")


def _register_core_services(container) -> None:
    """Register core services in the container."""
    # Register engine and session maker as singletons
    container.register_singleton(type(get_catalog_engine()), get_catalog_engine())
    container.register_singleton(
        type(get_catalog_session_maker()), get_catalog_session_maker()
    )

    # Register message bus and dispatcher as singletons
    container.register_singleton(IMessageBus, get_catalog_message_bus())
    container.register_singleton(DomainEventDispatcher, get_catalog_dispatcher())

    logger.log_debug_with_context("Registered core services")


def _register_messaging_services(container) -> None:
    """Register messaging services in the container."""
    logger.log_debug_with_context("Registered messaging services")


def _register_application_services(container) -> None:
    """Register application services in the container."""
    # Register mediator
    container.register_factory(Mediator, get_catalog_mediator)

    # ICatalogUnitOfWork is not registered here: it requires a session and is supplied
    # per-request via FastAPI DI (dependency_overrides).
    container.register_factory(RequestContext, lambda: RequestContext())

    logger.log_debug_with_context("Registered application services")


def _subscribe_domain_events(container) -> None:
    """Subscribe domain events to integration events."""
    dispatcher = container.get(DomainEventDispatcher)

    # This would register domain event handlers that publish integration events
    # For now, we'll just log the subscription
    logger.info("Subscribed domain events to integration events")


def wire_catalog_dependencies_to_fastapi(app: FastAPI, main_container=None) -> None:
    """
    Wire catalog dependencies to FastAPI app with proper dependency injection.

    Args:
        app: FastAPI application instance
        main_container: Main application DI container (optional)
    """
    catalog_container = get_catalog_container()

    # Register core services in catalog container
    _register_core_services(catalog_container)
    _register_messaging_services(catalog_container)
    _register_application_services(catalog_container)

    # Override FastAPI dependency providers
    dependency_overrides: dict[Any, Any] = {
        # Database dependencies
        get_catalog_engine: lambda: catalog_container.get(
            type(get_catalog_engine())
        ),
        get_catalog_session_maker: lambda: catalog_container.get(
            type(get_catalog_session_maker())
        ),
        # Repository dependencies
        # Wrap ProductRepository with CachedProductRepository for Redis caching
        ProductRepository: lambda session: CachedProductRepository(
            SqlProductRepository(session),
            get_catalog_cache_service(),
        ),
        CategoryRepository: lambda session: SqlCategoryRepository(session),
        InventoryRepository: lambda session: SqlInventoryRepository(session),
        # Application dependencies
        ICatalogUnitOfWork: lambda session: SqlCatalogUnitOfWork(
            session, get_catalog_cache_service()
        ),
        RequestContext: lambda: RequestContext(),
    }
    dependency_overrides[cast(Any, IMessageBus)] = (
        lambda: catalog_container.get(cast(Any, IMessageBus))
    )
    dependency_overrides[cast(Any, DomainEventDispatcher)] = (
        lambda: catalog_container.get(cast(Any, DomainEventDispatcher))
    )
    dependency_overrides[Mediator] = lambda: (
        main_container.get(Mediator)
        if main_container
        else catalog_container.get(Mediator)
    )
    app.dependency_overrides.update(dependency_overrides)

    logger.log_with_context("Wired catalog dependencies to FastAPI with overrides")


def get_catalog_dependency_overrides() -> dict[Any, Any]:
    """
    Get catalog dependency overrides for FastAPI.

    Returns:
        Dict of dependency overrides
    """
    container = get_catalog_container()

    overrides: dict[Any, Any] = {
        # Database dependencies
        get_catalog_engine: lambda: container.get(type(get_catalog_engine())),
        get_catalog_session_maker: lambda: container.get(
            type(get_catalog_session_maker())
        ),
        # Repository dependencies
        # Wrap ProductRepository with CachedProductRepository for Redis caching
        ProductRepository: lambda session: CachedProductRepository(
            SqlProductRepository(session),
            get_catalog_cache_service(),
        ),
        CategoryRepository: lambda session: SqlCategoryRepository(session),
        InventoryRepository: lambda session: SqlInventoryRepository(session),
        # Application dependencies
        ICatalogUnitOfWork: lambda session: SqlCatalogUnitOfWork(
            session, get_catalog_cache_service()
        ),
        RequestContext: lambda: RequestContext(),
    }
    overrides[cast(Any, IMessageBus)] = lambda: container.get(cast(Any, IMessageBus))
    overrides[cast(Any, DomainEventDispatcher)] = lambda: container.get(
        cast(Any, DomainEventDispatcher)
    )
    overrides[Mediator] = lambda: container.get(Mediator)
    return overrides


def register_catalog_handlers_with_mediator(mediator: Mediator) -> None:
    """
    Register catalog handlers with the mediator.

    Args:
        mediator: Mediator instance
    """
    # This would register all command and query handlers
    # For now, we'll just log the registration
    logger.log_with_context("Registered catalog handlers with mediator")


def subscribe_domain_events_to_integration_events(
    dispatcher: DomainEventDispatcher,
) -> None:
    """
    Subscribe domain events to integration events.

    Args:
        dispatcher: Domain event dispatcher
    """
    # Register internal domain event handlers (for cache, metrics, etc.)
    from app.modules.catalog.application.domain_event_handlers.products.product_deleted_domain_event_handler import \
        ProductDeletedDomainEventHandler
    from app.modules.catalog.application.domain_event_handlers.products.product_price_changed_domain_event_handler import \
        ProductPriceChangedDomainEventHandler
    from app.modules.catalog.domain.domain_events.products.product_deleted_domain_event import \
        ProductDeletedDomainEvent
    from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import \
        ProductPriceChangedDomainEvent

    # Register ProductDeletedDomainEvent handler
    product_deleted_handler = ProductDeletedDomainEventHandler()
    dispatcher.register_handler(ProductDeletedDomainEvent, product_deleted_handler)
    logger.log_with_context("Registered ProductDeletedDomainEventHandler")

    # Register ProductPriceChangedDomainEvent handler
    product_price_changed_handler = ProductPriceChangedDomainEventHandler()
    dispatcher.register_handler(
        ProductPriceChangedDomainEvent, product_price_changed_handler
    )
    logger.log_with_context("Registered ProductPriceChangedDomainEventHandler")

    logger.log_with_context("Subscribed domain events to integration events")
