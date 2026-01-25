"""Outbox pattern implementation for reliable messaging.

NOTE: This module is kept for backward compatibility.
New code should use app.core.messaging.outbox instead.
The core outbox provides the same functionality with better separation of concerns.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OutboxMessageStatus(str, Enum):
    """Status of outbox message."""

    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"


class OutboxMessage(BaseModel):
    """Outbox message for reliable messaging."""

    id: UUID = Field(..., description="Message ID")
    event_type: str = Field(..., description="Event type")
    event_data: dict[str, Any] = Field(..., description="Event data")
    status: OutboxMessageStatus = Field(
        default=OutboxMessageStatus.PENDING, description="Message status"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    processed_at: datetime | None = Field(None, description="Processing timestamp")
    retry_count: int = Field(default=0, description="Number of retries")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    error_message: str | None = Field(None, description="Error message if failed")
    correlation_id: str | None = Field(
        None, description="Correlation ID for tracing"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "event_data": self.event_data,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "correlation_id": self.correlation_id,
        }


class IOutboxWriter(ABC):
    """Interface for outbox writer."""

    @abstractmethod
    async def write_message(self, message: OutboxMessage) -> None:
        """
        Write message to outbox.

        Args:
            message: Outbox message to write
        """
        pass

    @abstractmethod
    async def mark_as_processing(self, message_id: UUID) -> None:
        """
        Mark message as processing.

        Args:
            message_id: Message ID
        """
        pass

    @abstractmethod
    async def mark_as_published(self, message_id: UUID) -> None:
        """
        Mark message as published.

        Args:
            message_id: Message ID
        """
        pass

    @abstractmethod
    async def mark_as_failed(self, message_id: UUID, error_message: str) -> None:
        """
        Mark message as failed.

        Args:
            message_id: Message ID
            error_message: Error message
        """
        pass


class IOutboxPublisher(ABC):
    """Interface for outbox publisher."""

    @abstractmethod
    async def publish_pending_messages(self) -> None:
        """Publish all pending messages from outbox."""
        pass

    @abstractmethod
    async def publish_message(self, message: OutboxMessage) -> None:
        """
        Publish a single message.

        Args:
            message: Message to publish
        """
        pass


class OutboxWriter(IOutboxWriter):
    """Outbox writer implementation."""

    def __init__(self, session: Any):
        """
        Initialize the outbox writer.

        Args:
            session: Database session
        """
        self.session = session

    async def write_message(self, message: OutboxMessage) -> None:
        """
        Write message to outbox.

        Args:
            message: Outbox message to write
        """
        try:
            # In a real implementation, this would save to database
            # For now, we'll just log it
            logger.info(f"Writing outbox message: {message.id}")

            # This would be something like:
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

    async def mark_as_processing(self, message_id: UUID) -> None:
        """
        Mark message as processing.

        Args:
            message_id: Message ID
        """
        logger.info(f"Marking outbox message as processing: {message_id}")
        # Implementation would update database record

    async def mark_as_published(self, message_id: UUID) -> None:
        """
        Mark message as published.

        Args:
            message_id: Message ID
        """
        logger.info(f"Marking outbox message as published: {message_id}")
        # Implementation would update database record

    async def mark_as_failed(self, message_id: UUID, error_message: str) -> None:
        """
        Mark message as failed.

        Args:
            message_id: Message ID
            error_message: Error message
        """
        logger.error(
            f"Marking outbox message as failed: {message_id}, error: {error_message}"
        )
        # Implementation would update database record


class OutboxPublisher(IOutboxPublisher):
    """Outbox publisher implementation."""

    def __init__(self, outbox_writer: IOutboxWriter, message_bus: Any):
        """
        Initialize the outbox publisher.

        Args:
            outbox_writer: Outbox writer
            message_bus: Message bus for publishing
        """
        self.outbox_writer = outbox_writer
        self.message_bus = message_bus

    async def publish_pending_messages(self) -> None:
        """Publish all pending messages from outbox."""
        try:
            # In a real implementation, this would query the database for pending messages
            # For now, we'll just log it
            logger.info("Publishing pending outbox messages")

            # This would be something like:
            # pending_messages = await self.session.query(OutboxORM).filter(
            #     OutboxORM.status == OutboxMessageStatus.PENDING
            # ).all()
            #
            # for message_record in pending_messages:
            #     message = OutboxMessage(
            #         id=message_record.id,
            #         event_type=message_record.event_type,
            #         event_data=json.loads(message_record.event_data),
            #         status=message_record.status,
            #         created_at=message_record.created_at,
            #         retry_count=message_record.retry_count,
            #         max_retries=message_record.max_retries,
            #         correlation_id=message_record.correlation_id,
            #     )
            #     await self.publish_message(message)

        except Exception as e:
            logger.error(f"Error publishing pending messages: {e}")
            raise

    async def publish_message(self, message: OutboxMessage) -> None:
        """
        Publish a single message.

        Args:
            message: Message to publish
        """
        try:
            # Mark as processing
            await self.outbox_writer.mark_as_processing(message.id)

            # Publish to message bus
            await self.message_bus.publish(message.event_data, message.event_type)

            # Mark as published
            await self.outbox_writer.mark_as_published(message.id)

            logger.info(f"Successfully published outbox message: {message.id}")

        except Exception as e:
            # Mark as failed
            await self.outbox_writer.mark_as_failed(message.id, str(e))
            logger.error(f"Failed to publish outbox message {message.id}: {e}")
            raise
