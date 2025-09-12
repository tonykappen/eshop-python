"""Database session management with async support."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings
from app.core.exceptions.base import DatabaseError
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)

# Create async engine with optimized connection pool
engine = create_async_engine(
    settings.database_connection_string,
    echo=settings.debug,
    # Connection pool configuration
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections when pool is full
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_reset_on_return="commit",  # Reset connection state on return
    # Performance optimizations
    future=True,  # Use SQLAlchemy 2.0 style
    use_insertmanyvalues=True,  # Optimize bulk inserts
    # Connection settings
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
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "total_connections": pool.checkedin() + pool.checkedout(),
        }
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
            f"✅ Database engine created and connection tested. Pool status: {pool_status}"
        )
    except Exception as e:
        logger.error(f"❌ Database engine creation failed: {e}")
        raise DatabaseError(
            message="Database engine creation failed", details=str(e)
        ) from e


async def close_db_engine() -> None:
    """Close database engine."""
    try:
        # Log final pool status before closing
        pool_status = await get_pool_status()
        logger.info(f"🗄️ Closing database engine. Final pool status: {pool_status}")

        await engine.dispose()
        logger.info("✅ Database engine closed")
    except Exception as e:
        logger.error(f"❌ Database engine close failed: {e}")
        raise DatabaseError(
            message="Database engine close failed", details=str(e)
        ) from e
