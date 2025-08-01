"""Integration events and outbox pattern implementation using faststream."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel, Field


class IntegrationEvent(BaseModel):
    """Base class for integration events."""

    id: UUID = Field(default_factory=uuid4)
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(default="")
    data: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class OutboxMessage(BaseModel):
    """Outbox message for reliable event publishing."""

    id: UUID = Field(default_factory=uuid4)
    type: str
    content: str
    created_on: datetime = Field(default_factory=datetime.utcnow)
    processed_on: datetime | None = None
    error: str | None = None

    class Config:
        arbitrary_types_allowed = True


class IIntegrationEventHandler:
    """Base interface for integration event handlers."""

    async def handle(self, event: IntegrationEvent) -> None:
        """Handle an integration event."""
        pass


class IEventPublisher:
    """Base interface for event publishers."""

    async def publish(self, event: IntegrationEvent) -> None:
        """Publish an integration event."""
        pass


class FastStreamEventPublisher(IEventPublisher):
    """FastStream-based event publisher."""

    def __init__(self, broker: RabbitBroker):
        self.broker = broker

    async def publish(self, event: IntegrationEvent) -> None:
        """Publish an integration event using FastStream."""
        await self.broker.publish(event.model_dump(), routing_key=event.event_type)


class FastStreamEventHandler(IIntegrationEventHandler):
    """FastStream-based event handler."""

    def __init__(self, handler_func):
        self.handler_func = handler_func

    async def handle(self, event: IntegrationEvent) -> None:
        """Handle an integration event using the provided handler function."""
        await self.handler_func(event)


class EventBus:
    """Event bus for managing integration events."""

    def __init__(self, broker: RabbitBroker):
        self.broker = broker
        self.app = FastStream(broker)
        self.handlers: dict[str, IIntegrationEventHandler] = {}

    def register_handler(
        self, event_type: str, handler: IIntegrationEventHandler
    ) -> None:
        """Register an event handler for a specific event type."""
        self.handlers[event_type] = handler

    async def publish(self, event: IntegrationEvent) -> None:
        """Publish an integration event."""
        publisher = FastStreamEventPublisher(self.broker)
        await publisher.publish(event)

    async def handle_event(self, event: IntegrationEvent) -> None:
        """Handle an integration event."""
        handler = self.handlers.get(event.event_type)
        if handler:
            await handler.handle(event)
        else:
            raise ValueError(
                f"No handler registered for event type: {event.event_type}"
            )

    def get_app(self) -> FastStream:
        """Get the FastStream application."""
        return self.app
