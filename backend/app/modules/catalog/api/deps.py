"""FastAPI dependencies for catalog module."""

import logging
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mediator.mediator import Mediator
from app.modules.catalog.application.context.request_context import RequestContext
from app.modules.catalog.application.uow import UnitOfWork
from app.modules.catalog.domain.product.repository import ProductRepository
from app.modules.catalog.infrastructure.persistence.db_session import get_session
from app.modules.catalog.infrastructure.persistence.repositories.product_repository import ProductRepositoryImpl

logger = logging.getLogger(__name__)


async def get_catalog_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get catalog database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with get_session() as session:
        yield session


async def get_product_repository(
    session: AsyncSession = Depends(get_catalog_session)
) -> ProductRepository:
    """
    Get product repository.
    
    Args:
        session: Database session
        
    Returns:
        ProductRepository: Product repository instance
    """
    return ProductRepositoryImpl(session)


async def get_unit_of_work(
    session: AsyncSession = Depends(get_catalog_session)
) -> UnitOfWork:
    """
    Get unit of work.
    
    Args:
        session: Database session
        
    Returns:
        UnitOfWork: Unit of work instance
    """
    return UnitOfWork(session)


async def get_mediator() -> Mediator:
    """
    Get mediator instance.
    
    Returns:
        Mediator: Mediator instance
    """
    # This would be injected from the DI container in a real implementation
    # For now, return a placeholder
    return None


async def get_request_context() -> RequestContext:
    """
    Get request context.
    
    Returns:
        RequestContext: Request context instance
    """
    # This would extract context from the request in a real implementation
    # For now, return a default context
    return RequestContext()


# Dependency aliases for easier imports
CatalogSession = Depends(get_catalog_session)
ProductRepo = Depends(get_product_repository)
CatalogUoW = Depends(get_unit_of_work)
CatalogMediator = Depends(get_mediator)
CatalogRequestContext = Depends(get_request_context)


