"""Catalog module wiring - router, DI, mediator registration."""

from fastapi import APIRouter

from app.core.di.container import Container
from app.core.mediator.mediator import Mediator

# Import commands and queries
from app.modules.catalog.application.features.products.commands.create_product.create_product_command import (
    CreateProductCommand,
)

# Import handlers for registration
from app.modules.catalog.application.features.products.commands.create_product.create_product_handler import (
    CreateProductHandler,
)
from app.modules.catalog.application.features.products.commands.delete_product.delete_product_command import (
    DeleteProductCommand,
)
from app.modules.catalog.application.features.products.commands.delete_product.delete_product_handler import (
    DeleteProductHandler,
)
from app.modules.catalog.application.features.products.commands.update_product.update_product_command import (
    UpdateProductCommand,
)
from app.modules.catalog.application.features.products.commands.update_product.update_product_handler import (
    UpdateProductHandler,
)
from app.modules.catalog.application.features.products.queries.get_product_by_id.handler import (
    GetProductByIdHandler,
)
from app.modules.catalog.application.features.products.queries.get_product_by_id.get_product_by_id_query import (
    GetProductByIdQuery,
)
from app.modules.catalog.application.features.products.queries.get_products.handler import (
    GetProductsHandler,
)
from app.modules.catalog.application.features.products.queries.get_products.get_products_query import (
    GetProductsQuery,
)
from app.modules.catalog.application.features.products.queries.get_products_by_category.handler import (
    GetProductsByCategoryHandler,
)
from app.modules.catalog.application.features.products.queries.get_products_by_category.get_products_by_category_query import (
    GetProductsByCategoryQuery,
)
from app.modules.catalog.infrastructure.messaging.domain_dispatcher import (
    DomainEventDispatcher,
)

# Import DI components
from app.modules.catalog.module_interface.di.products import (
    get_catalog_container,
    register_catalog_handlers_with_mediator,
    subscribe_domain_events_to_integration_events,
    wire_catalog_dependencies,
    wire_catalog_dependencies_to_fastapi,
)

# Import product router
from app.modules.catalog.router.product_router import router as product_router


def register_catalog_module(container: Container, mediator: Mediator) -> APIRouter:
    """
    Register the catalog module with dependency injection and mediator.

    Args:
        container: Dependency injection container
        mediator: Mediator for CQRS operations

    Returns:
        FastAPI router for the catalog module
    """
    # Get catalog container and wire dependencies
    catalog_container = get_catalog_container()
    wire_catalog_dependencies(catalog_container)

    # Register handlers with mediator
    register_catalog_handlers_with_mediator(mediator)
    mediator.register_handler(CreateProductCommand, CreateProductHandler())
    mediator.register_handler(UpdateProductCommand, UpdateProductHandler())
    mediator.register_handler(DeleteProductCommand, DeleteProductHandler())
    mediator.register_handler(GetProductByIdQuery, GetProductByIdHandler())
    mediator.register_handler(GetProductsQuery, GetProductsHandler())
    mediator.register_handler(
        GetProductsByCategoryQuery, GetProductsByCategoryHandler()
    )

    # Subscribe domain events to integration events
    dispatcher = catalog_container.get(DomainEventDispatcher)
    subscribe_domain_events_to_integration_events(dispatcher)

    # Create main router
    router = APIRouter(prefix="/api/v1", tags=["catalog"])

    # Include product router
    router.include_router(product_router)

    return router


def register_catalog_module_with_fastapi(
    app, container: Container, mediator: Mediator
) -> APIRouter:
    """
    Register the catalog module with FastAPI app and dependency injection.

    Args:
        app: FastAPI application instance
        container: Dependency injection container
        mediator: Mediator for CQRS operations

    Returns:
        FastAPI router for the catalog module
    """
    # Get catalog container and wire dependencies
    catalog_container = get_catalog_container()
    wire_catalog_dependencies_to_fastapi(app, container)

    # Register handlers with mediator
    register_catalog_handlers_with_mediator(mediator)
    mediator.register_handler(CreateProductCommand, CreateProductHandler())
    mediator.register_handler(UpdateProductCommand, UpdateProductHandler())
    mediator.register_handler(DeleteProductCommand, DeleteProductHandler())
    mediator.register_handler(GetProductByIdQuery, GetProductByIdHandler())
    mediator.register_handler(GetProductsQuery, GetProductsHandler())
    mediator.register_handler(
        GetProductsByCategoryQuery, GetProductsByCategoryHandler()
    )

    # Subscribe domain events to integration events
    dispatcher = catalog_container.get(DomainEventDispatcher)
    subscribe_domain_events_to_integration_events(dispatcher)

    # Create main router
    router = APIRouter(prefix="/api/v1", tags=["catalog"])

    # Include product router
    router.include_router(product_router)

    return router
