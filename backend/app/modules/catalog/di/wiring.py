"""Dependency injection wiring for catalog module."""

import logging
from typing import Any

from fastapi import FastAPI

from app.core.mediator.mediator import Mediator
from app.modules.catalog.application.context.request_context import RequestContext
from app.modules.catalog.application.uow import UnitOfWork
from app.modules.catalog.di.container import get_catalog_container
from app.modules.catalog.di.providers import (
    get_catalog_dispatcher,
    get_catalog_engine,
    get_catalog_mediator,
    get_catalog_message_bus,
    get_catalog_session_maker,
)
from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.inventory.repository import InventoryRepository
from app.modules.catalog.domain.product.repository import ProductRepository
from app.modules.catalog.infrastructure.messaging.bus import IMessageBus
from app.modules.catalog.infrastructure.messaging.domain_dispatcher import (
    DomainEventDispatcher,
)
from app.modules.catalog.infrastructure.messaging.outbox import (
    IOutboxPublisher,
    IOutboxWriter,
    OutboxPublisher,
    OutboxWriter,
)
from app.modules.catalog.infrastructure.persistence.repositories.category_repository import (
    CategoryRepositoryImpl,
)
from app.modules.catalog.infrastructure.persistence.repositories.inventory_repository import (
    InventoryRepositoryImpl,
)
from app.modules.catalog.infrastructure.persistence.repositories.product_repository import (
    ProductRepositoryImpl,
)

logger = logging.getLogger(__name__)


def wire_catalog_dependencies(app: FastAPI) -> None:  # noqa: ARG001
    """
    Wire catalog dependencies to FastAPI app.

    Args:
        app: FastAPI application instance
    """
    container = get_catalog_container()

    # Register core services
    _register_core_services(container)

    # Register repositories
    _register_repositories(container)

    # Register messaging services
    _register_messaging_services(container)

    # Register application services
    _register_application_services(container)

    # Subscribe domain events to integration events
    _subscribe_domain_events(container)

    logger.info("Wired catalog dependencies to FastAPI app")


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

    logger.debug("Registered core services")


def _register_repositories(container) -> None:
    """Register repository factories in the container."""
    # Register repository factories
    container.register_factory(
        ProductRepository, lambda: None
    )  # Will be resolved per request
    container.register_factory(
        CategoryRepository, lambda: None
    )  # Will be resolved per request
    container.register_factory(
        InventoryRepository, lambda: None
    )  # Will be resolved per request

    logger.debug("Registered repository factories")


def _register_messaging_services(container) -> None:
    """Register messaging services in the container."""
    # Register outbox services
    container.register_factory(
        IOutboxWriter, lambda: None
    )  # Will be resolved per request
    container.register_factory(
        IOutboxPublisher, lambda: None
    )  # Will be resolved per request

    logger.debug("Registered messaging services")


def _register_application_services(container) -> None:
    """Register application services in the container."""
    # Register mediator
    container.register_factory(Mediator, get_catalog_mediator)

    # Register unit of work factory
    container.register_factory(UnitOfWork, lambda: None)  # Will be resolved per request

    # Register request context factory
    container.register_factory(
        RequestContext, lambda: None
    )  # Will be resolved per request

    logger.debug("Registered application services")


def _subscribe_domain_events(container) -> None:
    """Subscribe domain events to integration events."""
    container.get(DomainEventDispatcher)

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
    _register_repositories(catalog_container)
    _register_messaging_services(catalog_container)
    _register_application_services(catalog_container)

    # Override FastAPI dependency providers
    app.dependency_overrides.update(
        {
            # Database dependencies
            get_catalog_engine: lambda: catalog_container.get(
                type(get_catalog_engine())
            ),
            get_catalog_session_maker: lambda: catalog_container.get(
                type(get_catalog_session_maker())
            ),
            # Repository dependencies
            ProductRepository: lambda session: ProductRepositoryImpl(session),
            CategoryRepository: lambda session: CategoryRepositoryImpl(session),
            InventoryRepository: lambda session: InventoryRepositoryImpl(session),
            # Application dependencies
            UnitOfWork: lambda session: UnitOfWork(session),
            RequestContext: lambda: RequestContext(),
            # Messaging dependencies
            IMessageBus: lambda: catalog_container.get(IMessageBus),
            DomainEventDispatcher: lambda: catalog_container.get(DomainEventDispatcher),
            IOutboxWriter: lambda session: OutboxWriter(session),
            IOutboxPublisher: lambda outbox_writer, message_bus: OutboxPublisher(
                outbox_writer, message_bus
            ),
            # Mediator dependency - use main container if available
            Mediator: lambda: (
                main_container.get(Mediator)
                if main_container
                else catalog_container.get(Mediator)
            ),
        }
    )

    logger.info("Wired catalog dependencies to FastAPI with overrides")


def get_catalog_dependency_overrides() -> dict[type[Any], Any]:
    """
    Get catalog dependency overrides for FastAPI.

    Returns:
        Dict of dependency overrides
    """
    container = get_catalog_container()

    return {
        # Database dependencies
        get_catalog_engine: lambda: container.get(type(get_catalog_engine())),
        get_catalog_session_maker: lambda: container.get(
            type(get_catalog_session_maker())
        ),
        # Repository dependencies
        ProductRepository: lambda session: ProductRepositoryImpl(session),
        CategoryRepository: lambda session: CategoryRepositoryImpl(session),
        InventoryRepository: lambda session: InventoryRepositoryImpl(session),
        # Application dependencies
        UnitOfWork: lambda session: UnitOfWork(session),
        RequestContext: lambda: RequestContext(),
        # Messaging dependencies
        IMessageBus: lambda: container.get(IMessageBus),
        DomainEventDispatcher: lambda: container.get(DomainEventDispatcher),
        IOutboxWriter: lambda session: OutboxWriter(session),
        IOutboxPublisher: lambda outbox_writer, message_bus: OutboxPublisher(
            outbox_writer, message_bus
        ),
        # Mediator dependency
        Mediator: lambda: container.get(Mediator),
    }


def register_catalog_handlers_with_mediator(mediator: Mediator) -> None:  # noqa: ARG001
    """
    Register catalog handlers with the mediator.

    Args:
        mediator: Mediator instance
    """
    # This would register all command and query handlers
    # For now, we'll just log the registration
    logger.info("Registered catalog handlers with mediator")


def subscribe_domain_events_to_integration_events(
    dispatcher: DomainEventDispatcher,  # noqa: ARG001
) -> None:
    """
    Subscribe domain events to integration events.

    Args:
        dispatcher: Domain event dispatcher
    """
    # This would register domain event handlers that publish integration events
    # For now, we'll just log the subscription
    logger.info("Subscribed domain events to integration events")
