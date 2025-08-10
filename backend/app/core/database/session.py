"""Database session management with async support."""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings
from app.core.exceptions.base import DatabaseError
from app.core.logging.logger import get_logger

logger = get_logger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_connection_string,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
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


async def create_db_engine() -> None:
    """Create and test database engine."""
    try:
        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database engine created and connection tested")
    except Exception as e:
        logger.error(f"❌ Database engine creation failed: {e}")
        raise DatabaseError(
            message="Database engine creation failed", details=str(e)
        ) from e


async def close_db_engine() -> None:
    """Close database engine."""
    try:
        await engine.dispose()
        logger.info("✅ Database engine closed")
    except Exception as e:
        logger.error(f"❌ Database engine close failed: {e}")
        raise DatabaseError(
            message="Database engine close failed", details=str(e)
        ) from e
