"""Outbox service - appends events to Outbox inside same TX."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID, uuid4

from app.core.messaging.integration_event import IntegrationEvent
from app.core.messaging.outbox.outbox_message_orm import OutboxMessage, OutboxMessageStatus
from app.core.context.request_context import get_trace_context, get_baggage

logger = logging.getLogger(__name__)


class IOutboxService(ABC):
    """Interface for outbox service."""

    @abstractmethod
    async def write_integration_event(self, event: IntegrationEvent | dict[str, Any]) -> None:
        """
        Write integration event to outbox within the same transaction.
        
        Args:
            event: Integration event to write
        """
        pass

    @abstractmethod
    async def write_message(self, message: OutboxMessage) -> None:
        """
        Write outbox message to database.
        
        Args:
            message: Outbox message to write
        """
        pass


class OutboxService(IOutboxService):
    """Outbox service implementation - writes events to outbox table."""

    def __init__(self, session: Any):
        """
        Initialize the outbox service.
        
        Args:
            session: Database session (must be part of the same transaction)
        """
        self.session = session

    async def write_integration_event(self, event: IntegrationEvent | dict[str, Any]) -> None:
        """
        Write integration event to outbox within the same transaction.
        
        Args:
            event: Integration event to write
        """
        try:
            # Get trace context and baggage for distributed tracing
            trace_context = get_trace_context()
            baggage = get_baggage()
            
            # Convert event to dict if it's an IntegrationEvent
            if isinstance(event, IntegrationEvent):
                event_data = event.model_dump()
                event_type = event.event_type
            else:
                event_data = event
                event_type = event.get("event_type", "unknown")
            
            # Create outbox message
            message = OutboxMessage(
                id=uuid4(),
                event_type=event_type,
                event_data=event_data,
                status=OutboxMessageStatus.PENDING,
                correlation_id=trace_context.get("trace_id") if trace_context else None,
                trace_context=trace_context or {},
                baggage=baggage or {},
            )
            
            # Write to database (within the same transaction)
            await self.write_message(message)
            
            logger.debug(f"Written integration event to outbox: {message.id} ({event_type})")
            
        except Exception as e:
            logger.error(f"Error writing integration event to outbox: {e}")
            raise

    async def write_message(self, message: OutboxMessage) -> None:
        """
        Write outbox message to database.
        
        Args:
            message: Outbox message to write
        """
        try:
            # Import here to avoid circular dependency
            # Modules will provide their own ORM model that implements this
            # For now, we'll log it - actual implementation should be in module-specific code
            logger.debug(f"Writing outbox message to database: {message.id}")
            
            # This should be implemented by modules using their ORM model
            # Example:
            # from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import OutboxORM
            # outbox_record = OutboxORM(
            #     id=message.id,
            #     event_type=message.event_type,
            #     event_data=json.dumps(message.event_data),
            #     status=message.status.value,
            #     created_at=message.created_at,
            #     retry_count=message.retry_count,
            #     max_retries=message.max_retries,
            #     correlation_id=message.correlation_id,
            # )
            # self.session.add(outbox_record)
            
        except Exception as e:
            logger.error(f"Error writing outbox message: {e}")
            raise

