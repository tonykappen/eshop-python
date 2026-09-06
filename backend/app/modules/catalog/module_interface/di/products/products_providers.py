"""Dependency injection providers for catalog module."""

from collections.abc import AsyncGenerator
from functools import lru_cache

from app.config.settings import settings
from app.core.context.application_context import RequestContext
from app.core.logging.base_logger import BaseLogger
from app.core.mediator.handler_registry import HandlerRegistry
from app.core.mediator.mediator import Mediator
from app.core.messaging.bus import IMessageBus, RabbitMQMessageBus
from app.core.messaging.domain_dispatcher import DomainEventDispatcher
from app.core.messaging.outbox import IOutboxService, OutboxService
from app.modules.catalog.application.services.catalog_cache_service import (
    CatalogCacheService, RedisCacheService)
from app.modules.catalog.application.unit_of_work import ICatalogUnitOfWork
from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.inventory.repository import InventoryRepository
from app.modules.catalog.domain.repositories.product.product_repository import \
    ProductRepository
from app.modules.catalog.infrastructure.persistence.db_context import (
    get_engine, get_session_maker)
from app.modules.catalog.infrastructure.persistence.repositories.products.redis.cached_product_repository import \
    CachedProductRepository
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import (
    SqlCategoryRepository, SqlInventoryRepository, SqlProductRepository)
from app.modules.catalog.infrastructure.persistence.unit_of_work import \
    SqlCatalogUnitOfWork
from app.modules.catalog.module_interface.di.products.products_containers import \
    get_catalog_container
from fastapi import Depends
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker)

logger = BaseLogger(__name__)


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


# Cache service provider
@lru_cache(maxsize=1)
def get_catalog_cache_service() -> CatalogCacheService:
    """
    Get catalog cache service.

    Returns:
        CatalogCacheService: Cache service instance
    """
    redis_cache_service = RedisCacheService()
    return CatalogCacheService(redis_cache_service)


# Repository providers
async def get_product_repository(
    session: AsyncSession = Depends(get_catalog_session),
    cache_service: CatalogCacheService = Depends(get_catalog_cache_service),
) -> ProductRepository:
    """
    Get product repository with Redis caching.

    Args:
        session: Database session
        cache_service: Cache service for Redis operations

    Returns:
        ProductRepository: Product repository instance with caching
    """
    # Wrap SQL repository with cached repository
    sql_repo = SqlProductRepository(session)
    return CachedProductRepository(sql_repo, cache_service)


async def get_category_repository(
    session: AsyncSession = Depends(get_catalog_session),
) -> CategoryRepository:
    """
    Get category repository.

    Args:
        session: Database session

    Returns:
        CategoryRepository: Category repository instance
    """
    return SqlCategoryRepository(session)


async def get_inventory_repository(
    session: AsyncSession = Depends(get_catalog_session),
) -> InventoryRepository:
    """
    Get inventory repository.

    Args:
        session: Database session

    Returns:
        InventoryRepository: Inventory repository instance
    """
    return SqlInventoryRepository(session)


# Application layer providers
async def get_unit_of_work(
    session: AsyncSession = Depends(get_catalog_session),
) -> ICatalogUnitOfWork:
    """
    Get unit of work.

    Args:
        session: Database session

    Returns:
        ICatalogUnitOfWork: Unit of work instance
    """
    return SqlCatalogUnitOfWork(session, get_catalog_cache_service())


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
        IMessageBus: Message bus instance (always RabbitMQ)
    """
    # Always use RabbitMQ - connection will be established in lifecycle handler
    bus = RabbitMQMessageBus(settings.rabbitmq_connection_string)
    return bus


@lru_cache(maxsize=1)
def get_catalog_dispatcher() -> DomainEventDispatcher:
    """
    Get catalog domain event dispatcher.

    Returns:
        DomainEventDispatcher: Domain event dispatcher instance
    """
    return DomainEventDispatcher()


async def get_catalog_outbox_service(
    session: AsyncSession = Depends(get_catalog_session),
) -> IOutboxService:
    """
    Get catalog outbox service (uses core outbox).

    Args:
        session: Database session

    Returns:
        IOutboxService: Outbox service instance
    """
    from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import \
        OutboxORM

    return OutboxService(session, outbox_orm_class=OutboxORM)


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
        mediator = Mediator(HandlerRegistry())
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


# UoW factory for handler injection (not FastAPI Depends)
def create_catalog_uow_factory():
    """Return a callable async-context-manager that yields ICatalogUnitOfWork.

    Usage in handlers::

        async with self._uow_factory() as uow:
            await uow.products.add(product)
            # commit happens on successful __aexit__
    """
    from contextlib import asynccontextmanager

    session_maker = get_catalog_session_maker()
    cache_service = get_catalog_cache_service()

    @asynccontextmanager
    async def factory():
        async with session_maker() as session:
            async with SqlCatalogUnitOfWork(session, cache_service) as uow:
                yield uow

    return factory


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
CatalogMediator = Depends(get_catalog_mediator)
CatalogContainer = Depends(get_catalog_container_provider)
