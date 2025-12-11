"""FastAPI dependencies for catalog module."""

import logging
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mediator.mediator import Mediator
from app.modules.catalog.application.context.request_context import RequestContext
from app.modules.catalog.application.unit_of_work import ICatalogUnitOfWork
from app.modules.catalog.domain.repositories.product.product_repository import ProductRepository
from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.inventory.repository import InventoryRepository
from app.modules.catalog.infrastructure.messaging.bus import IMessageBus
from app.core.messaging.outbox import IOutboxService, IOutboxDispatcher
from app.modules.catalog.infrastructure.messaging.outbox import OutboxWriter, OutboxPublisher  # Backward compatibility
from app.modules.catalog.infrastructure.messaging.domain_dispatcher import DomainEventDispatcher
from app.modules.catalog.module_interface.di.products.products_providers import (
    get_catalog_session,
    get_product_repository,
    get_category_repository,
    get_inventory_repository,
    get_unit_of_work,
    get_request_context,
    get_catalog_mediator,
    get_catalog_message_bus,
    get_catalog_dispatcher,
    get_catalog_outbox_service,
    get_catalog_outbox_writer,
    get_catalog_outbox_publisher,
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
CatalogOutboxService = Depends(get_catalog_outbox_service)
CatalogOutboxWriter = Depends(get_catalog_outbox_writer)  # Backward compatibility
CatalogOutboxPublisher = Depends(get_catalog_outbox_publisher)  # Backward compatibility


