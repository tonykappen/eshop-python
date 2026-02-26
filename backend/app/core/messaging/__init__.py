"""Messaging and integration events infrastructure."""

from app.core.messaging.bus import (
    IMessageBus,
    InMemoryMessageBus,
    RabbitMQMessageBus,
)
from app.core.messaging.domain_dispatcher import (
    DomainEventDispatcher,
    domain_event_dispatcher,
)
from app.core.messaging.outbox import (
    OutboxMessage,
    OutboxMessageStatus,
    OutboxService,
    IOutboxService,
    OutboxDispatcher,
    IOutboxDispatcher,
    OutboxPublisherWorker,
    OutboxWorkerRegistry,
    outbox_worker_registry,
    create_outbox_worker,
)

__all__ = [
    # Bus
    "IMessageBus",
    "InMemoryMessageBus",
    "RabbitMQMessageBus",
    # Domain dispatcher
    "DomainEventDispatcher",
    "domain_event_dispatcher",
    # Outbox
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
