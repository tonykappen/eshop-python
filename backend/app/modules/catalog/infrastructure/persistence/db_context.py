"""Database context for catalog module - combines config and session management."""

from collections.abc import AsyncGenerator

from app.core.logging.base_logger import BaseLogger
from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

logger = BaseLogger(__name__)


class CatalogDatabaseConfig(BaseSettings):
    """Database configuration for catalog module."""

    # Database connection
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/eshop",
        alias="CATALOG_DB_URL",
        description="Catalog database URL",
    )

    # Connection pool settings
    pool_size: int = Field(
        default=10,
        alias="CATALOG_DB_POOL_SIZE",
        description="Database connection pool size",
    )

    max_overflow: int = Field(
        default=20,
        alias="CATALOG_DB_MAX_OVERFLOW",
        description="Maximum overflow connections",
    )

    pool_timeout: int = Field(
        default=30,
        alias="CATALOG_DB_POOL_TIMEOUT",
        description="Pool timeout in seconds",
    )

    pool_recycle: int = Field(
        default=3600,
        alias="CATALOG_DB_POOL_RECYCLE",
        description="Pool recycle time in seconds",
    )

    # Connection settings
    echo: bool = Field(
        default=False, alias="CATALOG_DB_ECHO", description="Echo SQL statements"
    )

    echo_pool: bool = Field(
        default=False, alias="CATALOG_DB_ECHO_POOL", description="Echo pool events"
    )

    # Transaction settings
    isolation_level: str = Field(
        default="READ_COMMITTED",
        alias="CATALOG_DB_ISOLATION_LEVEL",
        description="Database isolation level",
    )

    # Migration settings
    migration_dir: str = Field(
        default="migrations",
        alias="CATALOG_MIGRATION_DIR",
        description="Migration directory",
    )

    # Schema settings
    schema_name: str = Field(
        default="catalog",
        alias="CATALOG_SCHEMA_NAME",
        description="Database schema name",
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global configuration instance
catalog_db_config = CatalogDatabaseConfig()

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
        logger.log_with_context("Created catalog database engine")

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
        logger.log_with_context("Created catalog session maker")

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
            logger.log_error_with_context("Database session error", error=e)
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
        logger.log_with_context("Closed catalog database engine")
