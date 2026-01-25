"""Catalog module router - using DI-integrated approach."""

from fastapi import APIRouter

from app.core.di.container import Container
from app.core.mediator.mediator import Mediator

# Import DI-integrated catalog module
from app.modules.catalog.module_interface.router import (
    register_catalog_module_with_fastapi,
)

# Import product router
from app.modules.catalog.router.product_router import router as product_router

# Create the main catalog router
router = APIRouter()

# Include the products router
router.include_router(product_router, tags=["catalog"])


def create_catalog_router(container: Container, mediator: Mediator) -> APIRouter:
    """
    Create catalog router with working endpoints.

    Args:
        container: Dependency injection container
        mediator: Mediator for CQRS operations

    Returns:
        FastAPI router for the catalog module
    """
    return router


def create_di_integrated_catalog_router(
    app, container: Container, mediator: Mediator
) -> APIRouter:
    """
    Create DI-integrated catalog router.

    Args:
        app: FastAPI application instance
        container: Dependency injection container
        mediator: Mediator for CQRS operations

    Returns:
        FastAPI router for the catalog module with DI integration
    """
    return register_catalog_module_with_fastapi(app, container, mediator)
