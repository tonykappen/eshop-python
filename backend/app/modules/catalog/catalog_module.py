"""Catalog module wiring - router, DI, mediator registration."""

from fastapi import APIRouter
from app.core.di.container import Container
from app.core.mediator.mediator import Mediator

# Import DI components
from app.modules.catalog.di.container import get_catalog_container
from app.modules.catalog.di.wiring import (
    wire_catalog_dependencies,
    wire_catalog_dependencies_to_fastapi,
    register_catalog_handlers_with_mediator,
    subscribe_domain_events_to_integration_events,
)
from app.modules.catalog.infrastructure.messaging.domain_dispatcher import DomainEventDispatcher

# Import feature routers
from app.modules.catalog.application.features.product.commands.create_product.endpoint import router as create_product_router
from app.modules.catalog.application.features.product.commands.update_product.endpoint import router as update_product_router
from app.modules.catalog.application.features.product.commands.delete_product.endpoint import router as delete_product_router
from app.modules.catalog.application.features.product.queries.get_product_by_id.endpoint import router as get_product_by_id_router
from app.modules.catalog.application.features.product.queries.get_products.endpoint import router as get_products_router

# Import handlers for registration
from app.modules.catalog.application.features.product.commands.create_product.handler import CreateProductHandler
from app.modules.catalog.application.features.product.commands.update_product.handler import UpdateProductHandler
from app.modules.catalog.application.features.product.commands.delete_product.handler import DeleteProductHandler
from app.modules.catalog.application.features.product.queries.get_product_by_id.handler import GetProductByIdHandler
from app.modules.catalog.application.features.product.queries.get_products.handler import GetProductsHandler

# Import commands and queries
from app.modules.catalog.application.features.product.commands.create_product.command import CreateProductCommand, CreateProductResult
from app.modules.catalog.application.features.product.commands.update_product.command import UpdateProductCommand, UpdateProductResult
from app.modules.catalog.application.features.product.commands.delete_product.command import DeleteProductCommand, DeleteProductResult
from app.modules.catalog.application.features.product.queries.get_product_by_id.query import GetProductByIdQuery, GetProductByIdResult
from app.modules.catalog.application.features.product.queries.get_products.query import GetProductsQuery, GetProductsResult


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
    
    # Subscribe domain events to integration events
    dispatcher = catalog_container.get(DomainEventDispatcher)
    subscribe_domain_events_to_integration_events(dispatcher)
    
    # Create main router
    router = APIRouter(prefix="/api/v1", tags=["catalog"])
    
    # Include feature routers
    router.include_router(create_product_router, prefix="/products")
    router.include_router(update_product_router, prefix="/products")
    router.include_router(delete_product_router, prefix="/products")
    router.include_router(get_product_by_id_router, prefix="/products")
    router.include_router(get_products_router, prefix="/products")
    
    return router


def register_catalog_module_with_fastapi(app, container: Container, mediator: Mediator) -> APIRouter:
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
    
    # Subscribe domain events to integration events
    dispatcher = catalog_container.get(DomainEventDispatcher)
    subscribe_domain_events_to_integration_events(dispatcher)
    
    # Create main router
    router = APIRouter(prefix="/api/v1", tags=["catalog"])
    
    # Include feature routers
    router.include_router(create_product_router, prefix="/products")
    router.include_router(update_product_router, prefix="/products")
    router.include_router(delete_product_router, prefix="/products")
    router.include_router(get_product_by_id_router, prefix="/products")
    router.include_router(get_products_router, prefix="/products")
    
    return router
