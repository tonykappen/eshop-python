"""Integration events and outbox pattern implementation using faststream."""

import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID, uuid4

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel, Field, field_validator


class IntegrationEvent(BaseModel):
    """Base class for integration events with auto-naming capabilities."""

    id: UUID = Field(default_factory=uuid4)
    creation_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: str = Field(default="")
    topic: str = Field(default="")
    source_module: str = Field(default="")
    routing_key: str = Field(default="")
    data: dict[str, Any] = Field(default_factory=dict)

    # Class-level configuration
    _auto_topic: ClassVar[bool] = True
    _topic_prefix: ClassVar[str] = "eshop"
    _routing_pattern: ClassVar[str] = "{prefix}.{module}.{event_type}"

    def __init__(self, **data: Any) -> None:
        """Initialize with auto-generated event metadata."""
        # Auto-set event_type from class name if not provided
        if not data.get("event_type"):
            data["event_type"] = self._generate_event_type()

        # Auto-set topic if not provided
        if not data.get("topic") and self._auto_topic:
            data["topic"] = self._generate_topic()

        # Auto-set source_module if not provided
        if not data.get("source_module"):
            data["source_module"] = self._extract_module_name()

        # Auto-set routing_key if not provided
        if not data.get("routing_key"):
            data["routing_key"] = self._generate_routing_key(
                data.get("event_type", ""),
                data.get("source_module", "")
            )

        super().__init__(**data)

    def _generate_event_type(self) -> str:
        """Generate event type from class name."""
        class_name = self.__class__.__name__
        # Remove 'Event' suffix if present and convert to snake_case
        if class_name.endswith("Event"):
            class_name = class_name[:-5]

        # Convert CamelCase to snake_case
        event_type = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
        return event_type

    def _extract_module_name(self) -> str:
        """Extract module name from the class module path."""
        module_path = self.__class__.__module__
        # Extract module name from path like 'eshop.modules.catalog.domain.events'
        parts = module_path.split(".")
        if "modules" in parts:
            module_idx = parts.index("modules")
            if module_idx + 1 < len(parts):
                return parts[module_idx + 1]  # e.g., 'catalog'

        # Fallback to last meaningful part
        return parts[-2] if len(parts) > 1 else parts[0]

    def _generate_topic(self) -> str:
        """Generate topic name from module and event type."""
        module_name = self._extract_module_name()
        event_type = self._generate_event_type()
        return f"{self._topic_prefix}.{module_name}.{event_type}"

    def _generate_routing_key(self, event_type: str, module_name: str) -> str:
        """Generate RabbitMQ routing key following the pattern."""
        return self._routing_pattern.format(
            prefix=self._topic_prefix,
            module=module_name or self._extract_module_name(),
            event_type=event_type or self._generate_event_type()
        )

    @field_validator("event_type", mode="before")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate and auto-generate event type if empty."""
        if not v:
            # This will be set in __init__, but we need a fallback
            class_name = cls.__name__
            if class_name.endswith("Event"):
                class_name = class_name[:-5]
            return re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
        return v

    @classmethod
    def from_domain_event(cls, domain_event: Any, **additional_data: Any) -> "IntegrationEvent":
        """Create integration event from domain event with enhanced metadata."""
        # Extract triggering class information
        triggering_class = domain_event.__class__.__name__
        triggering_module = domain_event.__class__.__module__

        data = {
            "event_type": cls._extract_event_name_from_class(triggering_class),
            "source_module": cls._extract_module_from_path(triggering_module),
            "data": {
                "domain_event_type": triggering_class,
                "domain_event_module": triggering_module,
                **domain_event.model_dump(),
                **additional_data
            }
        }

        return cls(**data)

    @staticmethod
    def _extract_event_name_from_class(class_name: str) -> str:
        """Extract clean event name from class name."""
        # Remove common suffixes and convert to snake_case
        name = class_name
        for suffix in ["Event", "Command", "Query", "Request", "Response"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    @staticmethod
    def _extract_module_from_path(module_path: str) -> str:
        """Extract module name from full module path."""
        parts = module_path.split(".")
        if "modules" in parts:
            module_idx = parts.index("modules")
            if module_idx + 1 < len(parts):
                return parts[module_idx + 1]
        return parts[-2] if len(parts) > 1 else "unknown"

    class Config:
        arbitrary_types_allowed = True


class ModuleIntegrationEvent(IntegrationEvent):
    """Integration event specific to a module with predefined routing."""

    def __init__(self, module_name: str, **data: Any) -> None:
        """Initialize with specific module context."""
        data["source_module"] = module_name
        super().__init__(**data)


class CatalogIntegrationEvent(ModuleIntegrationEvent):
    """Catalog module integration events."""

    def __init__(self, **data: Any) -> None:
        super().__init__(module_name="catalog", **data)


class BasketIntegrationEvent(ModuleIntegrationEvent):
    """Basket module integration events."""

    def __init__(self, **data: Any) -> None:
        super().__init__(module_name="basket", **data)


class OrderingIntegrationEvent(ModuleIntegrationEvent):
    """Ordering module integration events."""

    def __init__(self, **data: Any) -> None:
        super().__init__(module_name="ordering", **data)


class OutboxMessage(BaseModel):
    """Outbox message for reliable event publishing."""

    id: UUID = Field(default_factory=uuid4)
    type: str
    content: str
    routing_key: str = Field(default="")
    topic: str = Field(default="")
    created_on: datetime = Field(default_factory=lambda: datetime.now(UTC))
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

    async def publish(self, event: IntegrationEvent, routing_key: str | None = None) -> None:
        """Publish an integration event."""
        pass


class FastStreamEventPublisher(IEventPublisher):
    """FastStream-based event publisher with enhanced routing."""

    def __init__(self, broker: RabbitBroker):
        self.broker = broker

    async def publish(self, event: IntegrationEvent, routing_key: str | None = None) -> None:
        """Publish an integration event using FastStream with proper routing."""
        # Use provided routing key or auto-generated one
        key = routing_key or event.routing_key or event.event_type

        # Prepare message with metadata
        message = {
            **event.model_dump(),
            "_metadata": {
                "topic": event.topic,
                "routing_key": key,
                "source_module": event.source_module,
                "published_at": datetime.now(UTC).isoformat()
            }
        }

        await self.broker.publish(message, routing_key=key)


class FastStreamEventHandler(IIntegrationEventHandler):
    """FastStream-based event handler."""

    def __init__(self, handler_func: Callable[[IntegrationEvent], Any]) -> None:
        self.handler_func = handler_func

    async def handle(self, event: IntegrationEvent) -> None:
        """Handle an integration event using the provided handler function."""
        await self.handler_func(event)


class EventBus:
    """Event bus for managing integration events with enhanced routing."""

    def __init__(self, broker: RabbitBroker):
        self.broker = broker
        self.app = FastStream(broker)
        self.handlers: dict[str, IIntegrationEventHandler] = {}
        self.routing_patterns: dict[str, str] = {}

    def register_handler(
        self,
        event_type: str,
        handler: IIntegrationEventHandler,
        routing_pattern: str | None = None
    ) -> None:
        """Register an event handler for a specific event type with optional routing pattern."""
        self.handlers[event_type] = handler
        if routing_pattern:
            self.routing_patterns[event_type] = routing_pattern

    def register_module_handlers(self, module_name: str, handlers: dict[str, IIntegrationEventHandler]) -> None:
        """Register multiple handlers for a specific module."""
        for event_type, handler in handlers.items():
            # Auto-generate routing pattern for module
            routing_pattern = f"eshop.{module_name}.{event_type}"
            self.register_handler(event_type, handler, routing_pattern)

    async def publish(self, event: IntegrationEvent, routing_key: str | None = None) -> None:
        """Publish an integration event with enhanced routing."""
        publisher = FastStreamEventPublisher(self.broker)
        await publisher.publish(event, routing_key)

    async def publish_from_domain_event(self, domain_event: Any, **additional_data: Any) -> None:
        """Publish integration event created from domain event."""
        integration_event = IntegrationEvent.from_domain_event(domain_event, **additional_data)
        await self.publish(integration_event)

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

    def get_routing_key_for_event(self, event_type: str) -> str:
        """Get the routing key pattern for a specific event type."""
        return self.routing_patterns.get(event_type, f"eshop.*.{event_type}")
