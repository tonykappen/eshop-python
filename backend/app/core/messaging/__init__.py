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
from app.core.messaging.event_publisher import (
    CatalogEventPublisher,
    CatalogEventPublisherFactory,
)
from app.core.messaging.outbox import (
    IOutboxPublisher,
    IOutboxWriter,
    OutboxMessage,
    OutboxMessageStatus,
    OutboxPublisher,
    OutboxWriter,
)

__all__ = [
    # Bus
    "IMessageBus",
    "InMemoryMessageBus",
    "RabbitMQMessageBus",
    # Domain dispatcher
    "DomainEventDispatcher",
    "domain_event_dispatcher",
    # Event publisher
    "CatalogEventPublisher",
    "CatalogEventPublisherFactory",
    # Outbox (backward compatibility)
    "IOutboxPublisher",
    "IOutboxWriter",
    "OutboxMessage",
    "OutboxMessageStatus",
    "OutboxPublisher",
    "OutboxWriter",
]
