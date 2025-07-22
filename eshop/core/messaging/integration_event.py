"""Integration events and outbox pattern implementation."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..domain.entity import DomainEvent


class IntegrationEvent(BaseModel):
    """Base class for integration events."""
    
    id: UUID = Field(default_factory=uuid4)
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(default="")
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class OutboxMessage(BaseModel):
    """Outbox message for reliable event publishing."""
    
    id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    class Config:
        arbitrary_types_allowed = True


class IIntegrationEventHandler:
    """Base interface for integration event handlers."""
    
    async def handle(self, event: IntegrationEvent) -> None:
        """Handle an integration event."""
        raise NotImplementedError


class IEventPublisher:
    """Base interface for event publishers."""
    
    async def publish(self, event: IntegrationEvent) -> None:
        """Publish an integration event."""
        raise NotImplementedError
    
    async def publish_domain_event(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        raise NotImplementedError


class IOutboxProcessor:
    """Base interface for outbox processors."""
    
    async def process_pending_messages(self) -> None:
        """Process pending outbox messages."""
        raise NotImplementedError
    
    async def mark_as_processed(self, message_id: UUID) -> None:
        """Mark a message as processed."""
        raise NotImplementedError
    
    async def mark_as_failed(self, message_id: UUID, error: str) -> None:
        """Mark a message as failed."""
        raise NotImplementedError 