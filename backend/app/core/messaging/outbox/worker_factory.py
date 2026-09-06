"""Factory for creating outbox publisher workers for modules."""

from collections.abc import Callable
from typing import Any, AsyncContextManager, TypeVar

from app.core.logging.base_logger import BaseLogger
from app.core.messaging.outbox import OutboxPublisherWorker
from sqlalchemy.ext.asyncio import AsyncSession

logger = BaseLogger(__name__)

# Type variable for the ORM model
T = TypeVar("T")


def create_outbox_worker(
    module_name: str,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    message_bus: Any,
    outbox_orm_class: type[T],
    batch_size: int = 10,
    poll_interval: float = 5.0,
    max_retries: int = 3,
    auto_register: bool = True,
) -> OutboxPublisherWorker:
    """
    Create an outbox publisher worker for a module.

    Args:
        module_name: Name of the module (e.g., 'catalog', 'basket', 'ordering')
        session_factory: Factory function that returns an async context manager for database sessions
        message_bus: Message bus for publishing (must have async publish method)
        outbox_orm_class: The ORM model class for outbox messages
        batch_size: Number of messages to process in each batch
        poll_interval: Interval between polls in seconds
        max_retries: Maximum number of retries for failed messages
        auto_register: Whether to automatically register the worker with the global registry

    Returns:
        OutboxPublisherWorker instance
    """
    worker = OutboxPublisherWorker(
        session_factory=session_factory,
        message_bus=message_bus,
        outbox_orm_class=outbox_orm_class,
        batch_size=batch_size,
        poll_interval=poll_interval,
        max_retries=max_retries,
    )

    if auto_register:
        from app.core.messaging.outbox.worker_registry import \
            outbox_worker_registry

        outbox_worker_registry.register(module_name, worker)
        logger.log_with_context(
            "Created and registered outbox worker for module",
            context={"module_name": module_name},
        )

    return worker
