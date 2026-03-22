"""Database session management with async support."""

import os
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings
from app.core.exceptions.common_exceptions import DatabaseError
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)

_pool_size = int(os.environ.get("DB_POOL_SIZE", "10"))
_max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
_pool_recycle = int(os.environ.get("DB_POOL_RECYCLE", "300"))
_pool_timeout = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
_echo = os.environ.get("DB_ECHO", str(settings.debug)).lower() in ("true", "1", "yes")

engine = create_async_engine(
    settings.database_connection_string,
    echo=_echo,
    pool_size=_pool_size,
    max_overflow=_max_overflow,
    pool_pre_ping=True,
    pool_recycle=_pool_recycle,
    pool_timeout=_pool_timeout,
    pool_reset_on_return="commit",
    future=True,
    use_insertmanyvalues=True,
    connect_args=(
        {
            "server_settings": {
                "application_name": "eshop-python-api",
                "timezone": "UTC",
            }
        }
        if "postgresql" in settings.database_connection_string
        else {}
    ),
)

# Create async session factory with optimized settings
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects loaded after commit
    autoflush=False,  # Disable auto-flush for performance
    autocommit=False,  # Explicit transaction control
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency - matches .NET DbContext pattern."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_pool_status() -> dict[str, Any]:
    """Get connection pool status for monitoring."""
    try:
        pool = engine.pool
        status = {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.checkedin() + pool.checkedout(),
        }
        # Try to get invalid count if available (not all pool types support this)
        try:
            if hasattr(pool, "invalid"):
                status["invalid"] = pool.invalid()
            else:
                status["invalid"] = 0  # Default to 0 if not available
        except AttributeError:
            status["invalid"] = 0  # Default to 0 if attribute doesn't exist
        return status
    except Exception as e:
        logger.error(f"Failed to get pool status: {e}")
        return {"error": str(e)}


async def create_db_engine() -> None:
    """Create and test database engine."""
    try:
        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        # Log initial pool status
        pool_status = await get_pool_status()
        logger.info(
            f"[OK] Database engine created and connection tested. Pool status: {pool_status}"
        )
    except Exception as e:
        logger.error(f"[FAILED] Database engine creation failed: {e}")
        raise DatabaseError(
            message="Database engine creation failed", details=str(e)
        ) from e


async def close_db_engine() -> None:
    """Close database engine."""
    try:
        # Log final pool status before closing
        pool_status = await get_pool_status()
        logger.info(
            f"[DATABASE] Closing database engine. Final pool status: {pool_status}"
        )

        await engine.dispose()
        logger.info("[OK] Database engine closed")
    except Exception as e:
        logger.error(f"[FAILED] Database engine close failed: {e}")
        raise DatabaseError(
            message="Database engine close failed", details=str(e)
        ) from e
