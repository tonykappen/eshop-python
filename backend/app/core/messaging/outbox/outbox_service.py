"""Outbox service - appends events to Outbox inside same TX."""

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.core.context.request_context import get_baggage, get_trace_context
from app.core.logging.base_logger import BaseLogger
from app.core.messaging.integration_event import IntegrationEvent
from app.core.messaging.outbox.outbox_message_orm import (
    OutboxMessage,
    OutboxMessageStatus,
)

logger = BaseLogger(__name__)


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


_registered_outbox_orm_class: type[Any] | None = None


def register_outbox_orm(orm_class: type[Any]) -> None:
    """Register the outbox ORM class for the current module.

    Called by module bootstrap during startup so OutboxService never needs to
    auto-detect module-specific ORM classes.
    """
    global _registered_outbox_orm_class
    _registered_outbox_orm_class = orm_class
    logger.log_with_context(
        "Outbox ORM class registered",
        context={"orm_class": orm_class.__name__},
    )


def get_registered_outbox_orm() -> type[Any] | None:
    """Return the ORM class registered via register_outbox_orm."""
    return _registered_outbox_orm_class


class OutboxService(IOutboxService):
    """Outbox service implementation - writes events to outbox table."""

    def __init__(self, session: Any, outbox_orm_class: type[Any] | None = None):
        """
        Initialize the outbox service.

        Args:
            session: Database session (must be part of the same transaction)
            outbox_orm_class: ORM class for outbox messages. If not provided,
                            uses the class registered via register_outbox_orm().
        """
        self.session = session
        self.outbox_orm_class = (
            outbox_orm_class
            or _registered_outbox_orm_class
            or self._get_outbox_orm_class()
        )

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

            # Convert event to dict if it's an IntegrationEvent or Pydantic model
            # Use mode='json' to ensure UUIDs, datetime, etc. are JSON-serializable
            if isinstance(event, IntegrationEvent):
                event_data = event.model_dump(mode='json')
                event_type = event.event_type
            elif hasattr(event, "model_dump") and hasattr(event, "event_type"):
                # Handle Pydantic models that have event_type (like ProductDeletedIntegrationEvent)
                # Use mode='json' to ensure UUIDs, datetime, etc. are JSON-serializable
                event_data = event.model_dump(mode='json')
                event_type = event.event_type
            elif isinstance(event, dict):
                event_data = event
                event_type = event.get("event_type", "unknown")
            else:
                # Fallback: try to get event_type attribute or use class name
                if hasattr(event, "model_dump"):
                    event_data = event.model_dump(mode='json')
                else:
                    event_data = str(event)
                event_type = getattr(event, "event_type", getattr(event, "__class__", type(event)).__name__)

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

            logger.log_debug_with_context(
                "Written integration event to outbox",
                context={"message_id": str(message.id), "event_type": event_type}
            )

        except Exception as e:
            logger.log_error_with_context(
                "Error writing integration event to outbox",
                error=e
            )
            raise

    def _get_outbox_orm_class(self) -> type[Any] | None:
        """
        Try to auto-detect the outbox ORM class from common module locations.

        Returns:
            Outbox ORM class if found, None otherwise
        """
        try:
            # Try catalog module first (most common)
            from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import (
                OutboxORM,
            )

            return OutboxORM
        except ImportError:
            pass

        try:
            # Try ordering module
            from app.modules.ordering.infrastructure.orm_models import OutboxORM

            return OutboxORM
        except ImportError:
            pass

        try:
            # Try basket module
            from app.modules.basket.infrastructure.orm_models import OutboxORM

            return OutboxORM
        except ImportError:
            pass

        logger.log_warning_with_context(
            "Could not auto-detect outbox ORM class. "
            "Please provide outbox_orm_class parameter when initializing OutboxService."
        )
        return None

    async def write_message(self, message: OutboxMessage) -> None:
        """
        Write outbox message to database.

        Args:
            message: Outbox message to write
        """
        try:
            if self.outbox_orm_class is None:
                raise ValueError(
                    "Outbox ORM class not set. "
                    "Please provide outbox_orm_class when initializing OutboxService."
                )

            def _json_default(obj: Any) -> Any:
                if isinstance(obj, UUID):
                    return str(obj)
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                if isinstance(obj, Decimal):
                    return float(obj)
                raise TypeError(f"Type {type(obj)} not serializable")

            if isinstance(message.event_data, str):
                event_data_str = message.event_data
            elif isinstance(message.event_data, dict):
                event_data_str = json.dumps(message.event_data, default=_json_default)
            else:
                try:
                    if hasattr(message.event_data, "model_dump"):
                        payload = message.event_data.model_dump(mode="json")
                    elif hasattr(message.event_data, "dict"):
                        payload = message.event_data.dict()
                    else:
                        payload = message.event_data
                    event_data_str = json.dumps(payload, default=_json_default)
                except (TypeError, ValueError):
                    event_data_str = str(message.event_data)

            if isinstance(message.status, Enum):
                status_value = message.status.value
            elif isinstance(message.status, str):
                status_value = message.status
            else:
                status_value = str(message.status)

            created_at_naive = (
                message.created_at.replace(tzinfo=None)
                if message.created_at.tzinfo is not None
                else message.created_at
            )
            processed_at_naive = (
                message.processed_at.replace(tzinfo=None)
                if message.processed_at and message.processed_at.tzinfo is not None
                else message.processed_at
            )

            col_keys = {c.key for c in self.outbox_orm_class.__table__.columns}
            orm_kwargs: dict[str, Any] = {
                "id": message.id,
                "event_type": message.event_type,
                "event_data": event_data_str,
                "status": status_value,
                "created_at": created_at_naive,
                "retry_count": message.retry_count,
                "max_retries": message.max_retries,
                "correlation_id": message.correlation_id,
            }
            if "error_message" in col_keys:
                orm_kwargs["error_message"] = message.error_message
            if "trace_context" in col_keys:
                orm_kwargs["trace_context"] = (
                    message.trace_context if message.trace_context else None
                )
            if "baggage" in col_keys:
                orm_kwargs["baggage"] = message.baggage if message.baggage else None

            outbox_record = self.outbox_orm_class(**orm_kwargs)

            if processed_at_naive and "processed_at" in col_keys:
                outbox_record.processed_at = processed_at_naive

            self.session.add(outbox_record)

            logger.log_with_context(
                "Written outbox message to database",
                context={
                    "message_id": str(message.id),
                    "event_type": message.event_type,
                    "orm": self.outbox_orm_class.__name__,
                },
            )

        except Exception as e:
            logger.log_exception_detailed(
                "Error writing outbox message to database",
                exception=e
            )
            raise
