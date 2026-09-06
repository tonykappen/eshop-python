"""Ordering module DI providers."""

import logging
from collections.abc import AsyncGenerator
from functools import lru_cache

from app.config.settings import settings
from app.core.di.container import Container
from app.core.messaging.bus import IMessageBus, RabbitMQMessageBus
from app.modules.ordering.domain.repositories.order import IOrderRepository
from app.modules.ordering.infrastructure.persistence.db_context import (
    get_engine, get_session, get_session_maker)
from app.modules.ordering.infrastructure.persistence.repositories.orders.sql_order_repository import \
    SqlOrderRepository
from fastapi import Depends
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker)

logger = logging.getLogger(__name__)


def get_ordering_container() -> Container:
    """
    Get ordering module DI container.

    Returns:
        Container instance
    """
    container = Container()
    return container


@lru_cache(maxsize=1)
def get_ordering_message_bus() -> IMessageBus:
    """
    Get the ordering module RabbitMQ message bus singleton.

    Used by the ordering RabbitMQ consumer to declare its queue
    (e.g. ``basket-checkout-queue``) and bind it to the relevant
    integration-event exchange (e.g. ``basket.events``).

    Returns:
        IMessageBus: RabbitMQ-backed message bus instance.
    """
    return RabbitMQMessageBus(settings.rabbitmq_connection_string)


# Database providers
@lru_cache(maxsize=1)
def get_ordering_engine() -> AsyncEngine:
    """
    Get ordering database engine.

    Returns:
        AsyncEngine: Database engine
    """
    return get_engine()


@lru_cache(maxsize=1)
def get_ordering_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Get ordering session maker.

    Returns:
        async_sessionmaker: Session maker
    """
    return get_session_maker()


async def get_ordering_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get ordering database session with automatic transaction management.

    Yields:
        AsyncSession: Database session
    """
    async for session in get_session():
        yield session


# Repository providers
async def get_order_repository(
    session: AsyncSession = Depends(get_ordering_session),
) -> IOrderRepository:
    """
    Get order repository.

    Args:
        session: Database session

    Returns:
        IOrderRepository: Order repository instance
    """
    return SqlOrderRepository(session)


# Dependency aliases for easier imports
OrderingEngine = Depends(get_ordering_engine)
OrderingSessionMaker = Depends(get_ordering_session_maker)
OrderingSession = Depends(get_ordering_session)
OrderRepo = Depends(get_order_repository)
