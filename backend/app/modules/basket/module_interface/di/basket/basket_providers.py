"""Dependency injection providers for basket module."""

import logging
from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.cache.patterns import ICacheService
from app.core.cache.redis_cache_service import RedisCacheService
from app.core.mediator.mediator import IMediator, Mediator
from app.core.messaging.outbox.outbox_service import IOutboxService, OutboxService
from app.modules.basket.application.services.basket_cache_patterns import (
    BasketCachePatterns,
)
from app.modules.basket.application.services.basket_cache_service import (
    BasketCacheService,
)
from app.modules.basket.application.unit_of_work.basket_unit_of_work import (
    IBasketUnitOfWork,
)
from app.modules.basket.domain.repositories.basket import IBasketRepository
from app.modules.basket.infrastructure.persistence.db_context import (
    get_engine,
    get_session_maker,
)
from app.modules.basket.infrastructure.persistence.repositories.basket.cached_basket_repository import (
    CachedBasketRepository,
)
from app.modules.basket.infrastructure.persistence.repositories.basket.sql_basket_repository import (
    SqlBasketRepository,
)
from app.modules.basket.infrastructure.persistence.unit_of_work.sql_basket_unit_of_work import (
    SqlBasketUnitOfWork,
)
from app.modules.basket.module_interface.di.basket.basket_containers import (
    get_basket_container,
)

logger = logging.getLogger(__name__)


# Database providers
@lru_cache(maxsize=1)
def get_basket_engine() -> AsyncEngine:
    """
    Get basket database engine.

    Returns:
        AsyncEngine: Database engine
    """
    return get_engine()


@lru_cache(maxsize=1)
def get_basket_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Get basket session maker.

    Returns:
        async_sessionmaker: Session maker
    """
    return get_session_maker()


async def get_basket_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get basket database session with automatic transaction management.

    Yields:
        AsyncSession: Database session
    """
    from app.core.logging.base_logger import BaseLogger
    
    logger = BaseLogger(__name__)
    session_maker = get_basket_session_maker()
    
    # Validate session_maker is not a mock
    session_maker_is_mock = (
        hasattr(session_maker, '_mock_name') or 
        hasattr(session_maker, '_spec_class') or
        (hasattr(session_maker, '__class__') and 'Mock' in str(session_maker.__class__.__name__))
    )
    if session_maker_is_mock:
        error_msg = (
            f"CRITICAL: Session maker is a mock! Type: {type(session_maker)}. "
            f"This should not happen in production. Check basket dependency injection setup."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    async with session_maker() as session:
        # Validate session is not a mock
        session_is_mock = (
            hasattr(session, '_mock_name') or 
            hasattr(session, '_spec_class') or
            (hasattr(session, '__class__') and 'Mock' in str(session.__class__.__name__))
        )
        if session_is_mock:
            error_msg = (
                f"CRITICAL: Database session is a mock! Type: {type(session)}. "
                f"This should not happen in production. Check session maker configuration."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            yield session
            # Note: save_changes_async commits the transaction (matching .NET SaveChangesAsync)
            # If save_changes_async was called, the transaction is already committed
            # If it wasn't called and there are pending changes, commit them here
            if session.in_transaction():
                try:
                    # Check if there are any pending changes
                    has_changes = len(session.new) + len(session.dirty) + len(session.deleted) > 0
                    if has_changes:
                        await session.commit()
                except Exception as commit_error:
                    # If commit fails (e.g., already committed or no transaction), that's okay
                    # This can happen if save_changes_async already committed
                    error_msg = str(commit_error) if commit_error else "Unknown commit error"
                    if "already been committed" not in error_msg.lower() and "no transaction" not in error_msg.lower():
                        # Only log if it's not an expected error
                        logger.log_warning_with_context(
                            "Session commit in context manager failed",
                            context={"error": error_msg}
                        )
        except Exception as e:
            # Rollback on exception
            if session.in_transaction():
                try:
                    await session.rollback()
                except Exception:
                    # Ignore rollback errors (e.g., if already rolled back)
                    pass
            logger.log_error_with_context(
                "Basket database session error, transaction rolled back",
                error=e,
            )
            raise
        finally:
            await session.close()


# Repository providers
async def get_basket_repository(
    session: AsyncSession = Depends(get_basket_session),
    cache_service: ICacheService | None = None,
) -> IBasketRepository:
    """
    Get basket repository (with caching if cache service provided).

    Args:
        session: Database session
        cache_service: Optional cache service

    Returns:
        IBasketRepository: Basket repository instance
    """
    sql_repo = SqlBasketRepository(session)

    # If cache service is provided, wrap with cached repository
    if cache_service:
        basket_cache_service = BasketCacheService(cache_service)
        return CachedBasketRepository(
            repository=sql_repo,
            cache_service=basket_cache_service,
        )

    return sql_repo


# Application layer providers
async def get_basket_unit_of_work(
    session: AsyncSession = Depends(get_basket_session),
) -> IBasketUnitOfWork:
    """
    Get unit of work.

    Args:
        session: Database session

    Returns:
        IBasketUnitOfWork: Unit of work instance
    """
    return SqlBasketUnitOfWork(session)


async def get_basket_outbox_service(
    session: AsyncSession = Depends(get_basket_session),
) -> IOutboxService:
    """
    Get basket outbox service.

    Args:
        session: Database session

    Returns:
        IOutboxService: Outbox service instance
    """
    return OutboxService(session)


# Cache providers
@lru_cache(maxsize=1)
def get_basket_cache_service() -> BasketCacheService:
    """
    Get basket cache service.

    Returns:
        BasketCacheService: Cache service instance
    """
    redis_cache = RedisCacheService()
    return BasketCacheService(redis_cache)


# Mediator provider
async def get_basket_mediator(mediator: IMediator | None = None) -> IMediator:
    """
    Get basket mediator (uses main app mediator if provided).

    Args:
        mediator: Optional main app mediator

    Returns:
        IMediator: Mediator instance
    """
    if mediator:
        return mediator

    # Fallback: get from container or create new
    container = get_basket_container()
    try:
        return container.get(Mediator)
    except ValueError:
        # Create a new mediator instance if not in container
        from app.core.mediator.handler_registry import HandlerRegistry
        from app.core.mediator.mediator import Mediator

        handler_registry = HandlerRegistry()
        new_mediator = Mediator(handler_registry)
        container.register(Mediator, new_mediator)
        return new_mediator


# Dependency aliases for easier imports
BasketEngine = Depends(get_basket_engine)
BasketSessionMaker = Depends(get_basket_session_maker)
BasketSession = Depends(get_basket_session)
BasketRepo = Depends(get_basket_repository)
BasketUoW = Depends(get_basket_unit_of_work)
BasketOutboxService = Depends(get_basket_outbox_service)
BasketCache = Depends(get_basket_cache_service)
BasketMediator = Depends(get_basket_mediator)
