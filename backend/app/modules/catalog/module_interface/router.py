"""Catalog module wiring - router, DI, mediator registration."""

from app.core.di.container import Container
from app.core.mediator.mediator import Mediator
from app.core.messaging.domain_dispatcher import DomainEventDispatcher
from app.modules.catalog.module_interface.catalog_handler_registration import \
    register_catalog_handlers
from app.modules.catalog.module_interface.di.products import (
    get_catalog_container, subscribe_domain_events_to_integration_events,
    wire_catalog_dependencies, wire_catalog_dependencies_to_fastapi)
from app.modules.catalog.router.product_router import router as product_router
from fastapi import APIRouter


def register_catalog_module(container: Container, mediator: Mediator) -> APIRouter:
    """
    Register the catalog module with dependency injection and mediator.

    Handler registration goes through catalog_handler_registration (single source of truth).
    No handler wiring happens in this file.
    """
    catalog_container = get_catalog_container()
    wire_catalog_dependencies(catalog_container)

    register_catalog_handlers(mediator.handler_registry)

    dispatcher = catalog_container.get(DomainEventDispatcher)
    subscribe_domain_events_to_integration_events(dispatcher)

    from app.modules.catalog.application.transactions.register_interceptors import \
        register_catalog_commit_interceptors

    register_catalog_commit_interceptors()

    router = APIRouter(prefix="/api/v1", tags=["catalog"])
    router.include_router(product_router)
    return router


def register_catalog_module_with_fastapi(
    app, container: Container, mediator: Mediator
) -> APIRouter:
    """
    Register the catalog module with FastAPI app and dependency injection.

    Handler registration goes through catalog_handler_registration (single source of truth).
    No handler wiring happens in this file.
    """
    catalog_container = get_catalog_container()
    wire_catalog_dependencies_to_fastapi(app, container)

    register_catalog_handlers(mediator.handler_registry)

    dispatcher = catalog_container.get(DomainEventDispatcher)
    subscribe_domain_events_to_integration_events(dispatcher)

    from app.modules.catalog.application.transactions.register_interceptors import \
        register_catalog_commit_interceptors

    register_catalog_commit_interceptors()

    router = APIRouter(prefix="/api/v1", tags=["catalog"])
    router.include_router(product_router)
    return router
