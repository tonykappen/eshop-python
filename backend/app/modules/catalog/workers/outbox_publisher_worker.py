"""Catalog module wrapper for outbox publisher worker - uses core implementation."""

import logging
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.core.messaging.outbox import OutboxPublisherWorker
from app.modules.catalog.infrastructure.messaging.bus import RabbitMQMessageBus
from app.modules.catalog.infrastructure.persistence.db_context import (
    get_session_maker,
)
from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import OutboxORM

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_session_context():
    """Create an async context manager for database sessions."""
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


# Create message bus - always use RabbitMQ
message_bus = RabbitMQMessageBus(settings.rabbitmq_connection_string)

# Create catalog-specific worker instance using core implementation
outbox_publisher_worker = OutboxPublisherWorker(
    session_factory=get_session_context,
    message_bus=message_bus,
    outbox_orm_class=OutboxORM,
)
