"""Dependency injection module for catalog."""

from app.modules.catalog.di.container import CatalogContainer, get_catalog_container
from app.modules.catalog.di.providers import (
    get_catalog_dispatcher,
    get_catalog_engine,
    get_catalog_message_bus,
    get_catalog_outbox_publisher,
    get_catalog_outbox_writer,
    get_catalog_session_maker,
)
from app.modules.catalog.di.wiring import (
    wire_catalog_dependencies,
    wire_catalog_dependencies_to_fastapi,
)

__all__ = [
    "CatalogContainer",
    "get_catalog_container",
    "get_catalog_engine",
    "get_catalog_session_maker",
    "get_catalog_dispatcher",
    "get_catalog_message_bus",
    "get_catalog_outbox_writer",
    "get_catalog_outbox_publisher",
    "wire_catalog_dependencies",
    "wire_catalog_dependencies_to_fastapi",
]
