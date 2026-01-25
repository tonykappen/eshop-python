"""OutboxMessage ORM model - base structure for outbox messages."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field


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
    event_data: Dict[str, Any] = Field(..., description="Event data")
    status: OutboxMessageStatus = Field(default=OutboxMessageStatus.PENDING, description="Message status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    processed_at: datetime | None = Field(None, description="Processing timestamp")
    retry_count: int = Field(default=0, description="Number of retries")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    error_message: str | None = Field(None, description="Error message if failed")
    correlation_id: str | None = Field(None, description="Correlation ID for tracing")
    trace_context: Dict[str, Any] = Field(default_factory=dict, description="Trace context for distributed tracing")
    baggage: Dict[str, str] = Field(default_factory=dict, description="OTEL baggage for context propagation")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "event_data": self.event_data,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "correlation_id": self.correlation_id,
            "trace_context": self.trace_context,
            "baggage": self.baggage,
        }












