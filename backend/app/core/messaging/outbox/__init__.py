"""Transactional Outbox pattern for reliable messaging.

Use OutboxService, OutboxDispatcher, OutboxMessage (ORM), OutboxPublisherWorker,
worker_registry, and create_outbox_worker for all outbox usage.
"""

from app.core.messaging.outbox.outbox_dispatcher import (
    IOutboxDispatcher,
    OutboxDispatcher,
)
from app.core.messaging.outbox.outbox_message_orm import (
    OutboxMessage,
    OutboxMessageStatus,
)
from app.core.messaging.outbox.outbox_publisher_worker import OutboxPublisherWorker
from app.core.messaging.outbox.outbox_service import IOutboxService, OutboxService
from app.core.messaging.outbox.worker_factory import create_outbox_worker
from app.core.messaging.outbox.worker_registry import (
    OutboxWorkerRegistry,
    outbox_worker_registry,
)

__all__ = [
    "OutboxMessage",
    "OutboxMessageStatus",
    "OutboxService",
    "IOutboxService",
    "OutboxDispatcher",
    "IOutboxDispatcher",
    "OutboxPublisherWorker",
    "OutboxWorkerRegistry",
    "outbox_worker_registry",
    "create_outbox_worker",
]
