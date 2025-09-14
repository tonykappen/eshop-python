"""Catalog module wiring - router, DI, mediator registration."""

from fastapi import APIRouter
from app.core.di.container import Container
from app.core.mediator.mediator import Mediator

# Import feature routers
from .application.features.commands.create_product.endpoint import router as create_product_router
from .application.features.commands.update_product.endpoint import router as update_product_router
from .application.features.commands.delete_product.endpoint import router as delete_product_router
from .application.features.queries.get_product_by_id.endpoint import router as get_product_by_id_router
from .application.features.queries.get_products.endpoint import router as get_products_router

# Import handlers for registration
from .application.features.commands.create_product.handler import CreateProductHandler
from .application.features.commands.update_product.handler import UpdateProductHandler
from .application.features.commands.delete_product.handler import DeleteProductHandler
from .application.features.queries.get_product_by_id.handler import GetProductByIdHandler
from .application.features.queries.get_products.handler import GetProductsHandler

# Import commands and queries
from .application.features.commands.create_product.command import CreateProductCommand, CreateProductResult
from .application.features.commands.update_product.command import UpdateProductCommand, UpdateProductResult
from .application.features.commands.delete_product.command import DeleteProductCommand, DeleteProductResult
from .application.features.queries.get_product_by_id.query import GetProductByIdQuery, GetProductByIdResult
from .application.features.queries.get_products.query import GetProductsQuery, GetProductsResult


def register_catalog_module(container: Container, mediator: Mediator) -> APIRouter:
    """
    Register the catalog module with dependency injection and mediator.
    
    Args:
        container: Dependency injection container
        mediator: Mediator for CQRS operations
        
    Returns:
        FastAPI router for the catalog module
    """
    # Register handlers with mediator
    mediator.register_handler(CreateProductCommand, CreateProductHandler())
    mediator.register_handler(UpdateProductCommand, UpdateProductHandler())
    mediator.register_handler(DeleteProductCommand, DeleteProductHandler())
    mediator.register_handler(GetProductByIdQuery, GetProductByIdHandler())
    mediator.register_handler(GetProductsQuery, GetProductsHandler())
    
    # Create main router
    router = APIRouter(prefix="/api/v1", tags=["catalog"])
    
    # Include feature routers
    router.include_router(create_product_router, prefix="/products")
    router.include_router(update_product_router, prefix="/products")
    router.include_router(delete_product_router, prefix="/products")
    router.include_router(get_product_by_id_router, prefix="/products")
    router.include_router(get_products_router, prefix="/products")
    
    return router
