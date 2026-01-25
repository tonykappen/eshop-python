"""Product-specific dependency injection configuration."""

from app.modules.catalog.module_interface.di.products.products_containers import (
    CatalogContainer,
    get_catalog_container,
)
from app.modules.catalog.module_interface.di.products.products_providers import (
    get_catalog_dispatcher,
    get_catalog_engine,
    get_catalog_mediator,
    get_catalog_message_bus,
    get_catalog_outbox_publisher,
    get_catalog_outbox_writer,
    get_catalog_session_maker,
)
from app.modules.catalog.module_interface.di.products.products_wiring import (
    register_catalog_handlers_with_mediator,
    subscribe_domain_events_to_integration_events,
    wire_catalog_dependencies,
    wire_catalog_dependencies_to_fastapi,
)

__all__ = [
    "CatalogContainer",
    "get_catalog_container",
    "get_catalog_engine",
    "get_catalog_session_maker",
    "get_catalog_message_bus",
    "get_catalog_dispatcher",
    "get_catalog_outbox_writer",
    "get_catalog_outbox_publisher",
    "get_catalog_mediator",
    "wire_catalog_dependencies",
    "wire_catalog_dependencies_to_fastapi",
    "register_catalog_handlers_with_mediator",
    "subscribe_domain_events_to_integration_events",
]
