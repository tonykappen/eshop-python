"""Catalog module router - updated to use new DDD structure."""

from fastapi import APIRouter
from app.core.di.container import Container
from app.core.mediator.mediator import Mediator
from .catalog_module import register_catalog_module

# Create the main catalog router
router = APIRouter()


def create_catalog_router(container: Container, mediator: Mediator) -> APIRouter:
    """
    Create catalog router with proper DDD structure.
    
    Args:
        container: Dependency injection container
        mediator: Mediator for CQRS operations
        
    Returns:
        FastAPI router for the catalog module
    """
    return register_catalog_module(container, mediator)
