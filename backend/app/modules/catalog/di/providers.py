"""Dependency injection providers for catalog module."""

import logging
from typing import AsyncGenerator, Optional
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from fastapi import Depends

from app.core.mediator.mediator import Mediator
from app.modules.catalog.application.uow import UnitOfWork
from app.modules.catalog.application.context.request_context import RequestContext
from app.modules.catalog.domain.product.repository import ProductRepository
from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.inventory.repository import InventoryRepository
from app.modules.catalog.infrastructure.persistence.db_session import get_engine, get_session_maker
from app.modules.catalog.infrastructure.persistence.repositories.product_repository import ProductRepositoryImpl
from app.modules.catalog.infrastructure.persistence.repositories.category_repository import CategoryRepositoryImpl
from app.modules.catalog.infrastructure.persistence.repositories.inventory_repository import InventoryRepositoryImpl
from app.modules.catalog.infrastructure.messaging.bus import IMessageBus, InMemoryMessageBus, RabbitMQMessageBus
from app.modules.catalog.infrastructure.messaging.outbox import IOutboxWriter, IOutboxPublisher, OutboxWriter, OutboxPublisher
from app.modules.catalog.infrastructure.messaging.domain_dispatcher import DomainEventDispatcher
from app.modules.catalog.di.container import get_catalog_container

logger = logging.getLogger(__name__)


# Database providers
@lru_cache(maxsize=1)
def get_catalog_engine() -> AsyncEngine:
    """
    Get catalog database engine.
    
    Returns:
        AsyncEngine: Database engine
    """
    return get_engine()


@lru_cache(maxsize=1)
def get_catalog_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Get catalog session maker.
    
    Returns:
        async_sessionmaker: Session maker
    """
    return get_session_maker()


async def get_catalog_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get catalog database session.
    
    Yields:
        AsyncSession: Database session
    """
    session_maker = get_catalog_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Repository providers
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


async def get_category_repository(
    session: AsyncSession = Depends(get_catalog_session)
) -> CategoryRepository:
    """
    Get category repository.
    
    Args:
        session: Database session
        
    Returns:
        CategoryRepository: Category repository instance
    """
    return CategoryRepositoryImpl(session)


async def get_inventory_repository(
    session: AsyncSession = Depends(get_catalog_session)
) -> InventoryRepository:
    """
    Get inventory repository.
    
    Args:
        session: Database session
        
    Returns:
        InventoryRepository: Inventory repository instance
    """
    return InventoryRepositoryImpl(session)


# Application layer providers
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


async def get_request_context() -> RequestContext:
    """
    Get request context.
    
    Returns:
        RequestContext: Request context instance
    """
    # This would extract context from the request in a real implementation
    # For now, return a default context
    return RequestContext()


# Messaging providers
@lru_cache(maxsize=1)
def get_catalog_message_bus() -> IMessageBus:
    """
    Get catalog message bus.
    
    Returns:
        IMessageBus: Message bus instance
    """
    # In a real implementation, this would be configured based on environment
    # For now, return in-memory bus
    return InMemoryMessageBus()


@lru_cache(maxsize=1)
def get_catalog_dispatcher() -> DomainEventDispatcher:
    """
    Get catalog domain event dispatcher.
    
    Returns:
        DomainEventDispatcher: Domain event dispatcher instance
    """
    return DomainEventDispatcher()


async def get_catalog_outbox_writer(
    session: AsyncSession = Depends(get_catalog_session)
) -> IOutboxWriter:
    """
    Get catalog outbox writer.
    
    Args:
        session: Database session
        
    Returns:
        IOutboxWriter: Outbox writer instance
    """
    return OutboxWriter(session)


async def get_catalog_outbox_publisher(
    outbox_writer: IOutboxWriter = Depends(get_catalog_outbox_writer),
    message_bus: IMessageBus = Depends(get_catalog_message_bus)
) -> IOutboxPublisher:
    """
    Get catalog outbox publisher.
    
    Args:
        outbox_writer: Outbox writer
        message_bus: Message bus
        
    Returns:
        IOutboxPublisher: Outbox publisher instance
    """
    return OutboxPublisher(outbox_writer, message_bus)


# Mediator provider
async def get_catalog_mediator() -> Mediator:
    """
    Get catalog mediator.
    
    Returns:
        Mediator: Mediator instance
    """
    # This would be injected from the DI container in a real implementation
    # For now, return a placeholder
    container = get_catalog_container()
    mediator = container.get_optional(Mediator)
    if mediator is None:
        # Create a new mediator instance
        mediator = Mediator()
        container.register(Mediator, mediator)
    return mediator


# Container-based providers
def get_catalog_container_provider():
    """
    Get catalog container provider.
    
    Returns:
        CatalogContainer: Container instance
    """
    return get_catalog_container()


# Dependency aliases for easier imports
CatalogEngine = Depends(get_catalog_engine)
CatalogSessionMaker = Depends(get_catalog_session_maker)
CatalogSession = Depends(get_catalog_session)
ProductRepo = Depends(get_product_repository)
CategoryRepo = Depends(get_category_repository)
InventoryRepo = Depends(get_inventory_repository)
CatalogUoW = Depends(get_unit_of_work)
CatalogRequestContext = Depends(get_request_context)
CatalogMessageBus = Depends(get_catalog_message_bus)
CatalogDispatcher = Depends(get_catalog_dispatcher)
CatalogOutboxWriter = Depends(get_catalog_outbox_writer)
CatalogOutboxPublisher = Depends(get_catalog_outbox_publisher)
CatalogMediator = Depends(get_catalog_mediator)
CatalogContainer = Depends(get_catalog_container_provider)
