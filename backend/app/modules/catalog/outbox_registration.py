"""Explicit outbox worker registration for the catalog module.

Workers are registered here and invoked from application startup (composition root)
rather than via module import side effects, making initialization deterministic.
"""

from contextlib import asynccontextmanager

from app.core.logging.base_logger import BaseLogger
from app.core.messaging.outbox import create_outbox_worker
from app.modules.catalog.infrastructure.persistence.db_context import \
    get_session_maker
from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import \
    OutboxORM
from app.modules.catalog.module_interface.di.products.products_providers import \
    get_catalog_message_bus

logger = BaseLogger(__name__)


@asynccontextmanager
async def _get_session_context():
    """Create an async context manager for database sessions (used by outbox worker)."""
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


def register_outbox_worker() -> None:
    """
    Create and register the catalog outbox publisher worker with the global registry.

    Call this during application startup (e.g. from a lifecycle callback) so that
    the worker is available when messaging_handler starts outbox workers.
    Uses the same message bus instance as DI so lifecycle connect() applies to it.
    """
    message_bus = get_catalog_message_bus()
    create_outbox_worker(
        module_name="catalog",
        session_factory=_get_session_context,
        message_bus=message_bus,
        outbox_orm_class=OutboxORM,
        auto_register=True,
    )
    logger.log_debug_with_context("Registered catalog outbox worker")
