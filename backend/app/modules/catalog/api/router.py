"""Catalog module router - using working endpoints approach."""

from fastapi import APIRouter
from app.core.di.container import Container
from app.core.mediator.mediator import Mediator

# Import the working endpoints module
from .endpoints import products

# Create the main catalog router
router = APIRouter()

# Include the products router
router.include_router(products.router, tags=["catalog"])


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
