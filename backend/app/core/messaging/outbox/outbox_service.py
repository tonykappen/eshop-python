"""Outbox service - appends events to Outbox inside same TX."""

import logging
from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

from app.core.context.request_context import get_baggage, get_trace_context
from app.core.messaging.integration_event import IntegrationEvent
from app.core.messaging.outbox.outbox_message_orm import (
    OutboxMessage,
    OutboxMessageStatus,
)

logger = logging.getLogger(__name__)


class IOutboxService(ABC):
    """Interface for outbox service."""

    @abstractmethod
    async def write_integration_event(
        self, event: IntegrationEvent | dict[str, Any]
    ) -> None:
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

    async def write_integration_event(
        self, event: IntegrationEvent | dict[str, Any]
    ) -> None:
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

            logger.debug(
                f"Written integration event to outbox: {message.id} ({event_type})"
            )

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
            import json
            
            # Try to determine which schema to use based on session metadata
            # Check if session has a bind that can tell us the schema
            schema_name = "basket"  # Default to basket schema
            
            # Try to import basket outbox ORM first (most common for checkout)
            try:
                from app.modules.basket.infrastructure.persistence.orm.basket.outbox_orm import (
                    OutboxORM,
                )
                schema_name = "basket"
            except ImportError:
                # Fallback to catalog if basket not available
                try:
                    from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import (
                        OutboxORM,
                    )
                    schema_name = "catalog"
                except ImportError:
                    logger.error("No outbox ORM model found for basket or catalog schema")
                    raise ValueError("Outbox ORM model not found")

            # Get status value - handle both enum and string
            status_value = message.status
            if hasattr(message.status, 'value'):
                status_value = message.status.value
            elif isinstance(message.status, str):
                status_value = message.status
            else:
                status_value = str(message.status)
            
            # Serialize event_data to JSON, handling UUIDs and other non-serializable types
            def json_serializer(obj):
                """JSON serializer for objects not serializable by default json code"""
                from uuid import UUID
                from datetime import datetime, date
                from decimal import Decimal
                
                if isinstance(obj, UUID):
                    return str(obj)
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                if isinstance(obj, Decimal):
                    return float(obj)
                raise TypeError(f"Type {type(obj)} not serializable")
            
            # Serialize event_data
            if isinstance(message.event_data, dict):
                event_data_json = json.dumps(message.event_data, default=json_serializer)
            elif isinstance(message.event_data, str):
                event_data_json = message.event_data
            else:
                # Try to convert to dict first, then serialize
                try:
                    if hasattr(message.event_data, 'model_dump'):
                        # Pydantic model
                        event_data_dict = message.event_data.model_dump()
                        event_data_json = json.dumps(event_data_dict, default=json_serializer)
                    elif hasattr(message.event_data, 'dict'):
                        # Pydantic v1
                        event_data_dict = message.event_data.dict()
                        event_data_json = json.dumps(event_data_dict, default=json_serializer)
                    else:
                        event_data_json = json.dumps(message.event_data, default=json_serializer)
                except (TypeError, ValueError):
                    event_data_json = str(message.event_data)
            
            # Create outbox record
            outbox_record = OutboxORM(
                id=message.id,
                event_type=message.event_type,
                event_data=event_data_json,
                status=status_value,
                created_at=message.created_at,
                retry_count=message.retry_count,
                max_retries=message.max_retries,
                error_message=message.error_message,
                correlation_id=message.correlation_id,
                trace_context=message.trace_context if hasattr(message, 'trace_context') else None,
                baggage=message.baggage if hasattr(message, 'baggage') else None,
            )
            
            # Add to session (will be committed with the transaction)
            self.session.add(outbox_record)
            
            logger.debug(
                f"Added outbox message to session: {message.id} ({message.event_type}) in {schema_name} schema"
            )

        except Exception as e:
            logger.error(f"Error writing outbox message: {e}")
            raise
