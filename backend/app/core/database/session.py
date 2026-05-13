"""Database session management with async support."""

import asyncio
import os
import threading
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event, text
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

_pool_event_lock = threading.Lock()
_pool_checkout_event_count = 0
_pool_checkin_event_count = 0


def _sync_pool_metrics(pool: Any) -> tuple[int, int, int] | None:
    """Return (pool_size, checked_out, overflow) or None if the pool has no sizing API."""
    try:
        pool_size = pool.size()
        checked_out = pool.checkedout()
        overflow = pool.overflow()
    except AttributeError:
        return None
    return pool_size, checked_out, overflow


def _on_pool_checkout(dbapi_conn: Any, connection_record: Any, connection_proxy: Any) -> None:
    global _pool_checkout_event_count
    with _pool_event_lock:
        _pool_checkout_event_count += 1
        metrics = _sync_pool_metrics(engine.sync_engine.pool)
        if metrics is None:
            return
        pool_size, checked_out, overflow = metrics
        if checked_out >= pool_size:
            logger.warning(
                "Connection pool exhaustion risk: checked_out=%s >= pool_size=%s, "
                "overflow=%s, total_checkout_events=%s",
                checked_out,
                pool_size,
                overflow,
                _pool_checkout_event_count,
            )


def _on_pool_checkin(dbapi_conn: Any, connection_record: Any) -> None:
    global _pool_checkin_event_count
    with _pool_event_lock:
        _pool_checkin_event_count += 1


event.listen(engine.sync_engine.pool, "checkout", _on_pool_checkout)
event.listen(engine.sync_engine.pool, "checkin", _on_pool_checkin)

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


async def log_pool_health() -> None:
    """Log a warning when the pool is near exhaustion (80% utilization or overflow)."""
    try:

        def _evaluate() -> tuple[int, int, int] | None:
            return _sync_pool_metrics(engine.sync_engine.pool)

        metrics = await asyncio.to_thread(_evaluate)
        if metrics is None:
            return
        pool_size, checked_out, overflow = metrics
        near_exhaustion = checked_out > pool_size * 0.8 or overflow > 0
        if near_exhaustion:
            logger.warning(
                "Database pool near exhaustion: checked_out=%s, pool_size=%s, "
                "threshold_80pct=%.1f, overflow=%s, checkout_events=%s, checkin_events=%s",
                checked_out,
                pool_size,
                pool_size * 0.8,
                overflow,
                _pool_checkout_event_count,
                _pool_checkin_event_count,
            )
    except Exception as e:
        logger.error("Failed to log pool health: %s", e)


async def get_pool_status() -> dict[str, Any]:
    """Get connection pool status for monitoring."""
    try:
        pool = engine.sync_engine.pool
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
