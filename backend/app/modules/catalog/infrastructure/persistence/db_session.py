"""Database session configuration for catalog module."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.modules.catalog.infrastructure.persistence.db_config import catalog_db_config

logger = logging.getLogger(__name__)

# Global engine and session maker
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get the database engine.

    Returns:
        AsyncEngine instance
    """
    global _engine

    if _engine is None:
        _engine = create_async_engine(
            catalog_db_config.database_url,
            pool_size=catalog_db_config.pool_size,
            max_overflow=catalog_db_config.max_overflow,
            pool_timeout=catalog_db_config.pool_timeout,
            pool_recycle=catalog_db_config.pool_recycle,
            echo=catalog_db_config.echo,
            echo_pool=catalog_db_config.echo_pool,
            isolation_level=catalog_db_config.isolation_level,
        )
        logger.info("Created catalog database engine")

    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Get the session maker.

    Returns:
        async_sessionmaker instance
    """
    global _session_maker

    if _session_maker is None:
        engine = get_engine()
        _session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Created catalog session maker")

    return _session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session.

    Yields:
        AsyncSession instance
    """
    session_maker = get_session_maker()

    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def close_engine() -> None:
    """Close the database engine."""
    global _engine, _session_maker

    if _engine:
        await _engine.dispose()
        _engine = None
        _session_maker = None
        logger.info("Closed catalog database engine")
