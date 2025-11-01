"""FastAPI dependencies for catalog module."""

import logging

from fastapi import Depends

from app.modules.catalog.di.providers import (
    get_catalog_dispatcher,
    get_catalog_mediator,
    get_catalog_message_bus,
    get_catalog_outbox_publisher,
    get_catalog_outbox_writer,
    get_catalog_session,
    get_category_repository,
    get_inventory_repository,
    get_product_repository,
    get_request_context,
    get_unit_of_work,
)

logger = logging.getLogger(__name__)


# Re-export providers from DI module
# These are now properly implemented in the DI providers module

# Dependency aliases for easier imports
CatalogSession = Depends(get_catalog_session)
ProductRepo = Depends(get_product_repository)
CategoryRepo = Depends(get_category_repository)
InventoryRepo = Depends(get_inventory_repository)
CatalogUoW = Depends(get_unit_of_work)
CatalogRequestContext = Depends(get_request_context)
CatalogMediator = Depends(get_catalog_mediator)
CatalogMessageBus = Depends(get_catalog_message_bus)
CatalogDispatcher = Depends(get_catalog_dispatcher)
CatalogOutboxWriter = Depends(get_catalog_outbox_writer)
CatalogOutboxPublisher = Depends(get_catalog_outbox_publisher)
