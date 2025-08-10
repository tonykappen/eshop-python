"""Tests for the messaging module."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel

from app.core.messaging.integration_event import (
    BasketIntegrationEvent,
    CatalogIntegrationEvent,
    EventBus,
    FastStreamEventHandler,
    FastStreamEventPublisher,
    IIntegrationEventHandler,
    IntegrationEvent,
    ModuleIntegrationEvent,
    OrderingIntegrationEvent,
    OutboxMessage,
)


@pytest.mark.no_collect
class TestDomainEvent(BaseModel):
    """Test domain event for messaging tests."""

    id: UUID
    name: str
    value: int


@pytest.mark.no_collect
class TestIntegrationEvent:
    """Test IntegrationEvent class."""

    def test_integration_event_default_values(self) -> None:
        """Test IntegrationEvent with default values."""
        event = IntegrationEvent()

        assert isinstance(event.id, UUID)
        assert isinstance(event.creation_date, datetime)
        assert event.event_type == "integration"
        assert event.topic == "app.messaging.integration"
        assert event.source_module == "messaging"
        assert event.routing_key == "app.messaging.integration"
        assert event.data == {}

    def test_integration_event_custom_values(self) -> None:
        """Test IntegrationEvent with custom values."""
        custom_id = uuid4()
        custom_date = datetime.now(UTC)

        event = IntegrationEvent(
            id=custom_id,
            creation_date=custom_date,
            event_type="custom_event",
            topic="custom.topic",
            source_module="custom_module",
            routing_key="custom.routing.key",
            data={"key": "value"},
        )

        assert event.id == custom_id
        assert event.creation_date == custom_date
        assert event.event_type == "custom_event"
        assert event.topic == "custom.topic"
        assert event.source_module == "custom_module"
        assert event.routing_key == "custom.routing.key"
        assert event.data == {"key": "value"}

    def test_generate_event_type_from_class_name(self) -> None:
        """Test event type generation from class name."""

        class TestProductCreatedEvent(IntegrationEvent):
            pass

        event = TestProductCreatedEvent()
        assert event.event_type == "test_product_created"

    def test_generate_event_type_with_event_suffix(self) -> None:
        """Test event type generation with Event suffix."""

        class ProductCreatedEvent(IntegrationEvent):
            pass

        event = ProductCreatedEvent()
        assert event.event_type == "product_created"

    def test_extract_module_name_from_path(self) -> None:
        """Test module name extraction from module path."""

        class TestEvent(IntegrationEvent):
            pass

        # Mock the module path
        with patch.object(
            TestEvent, "__module__", "app.modules.catalog.domain.events"
        ):
            event = TestEvent()
            assert event.source_module == "catalog"

    def test_extract_module_name_fallback(self) -> None:
        """Test module name extraction fallback."""

        class TestEvent(IntegrationEvent):
            pass

        # Mock the module path to test fallback
        with patch.object(TestEvent, "__module__", "app.core.messaging"):
            event = TestEvent()
            assert event.source_module == "core"

    def test_generate_topic(self) -> None:
        """Test topic generation."""

        class TestEvent(IntegrationEvent):
            pass

        with patch.object(
            TestEvent, "__module__", "app.modules.catalog.domain.events"
        ):
            event = TestEvent()
            assert event.topic == "app.catalog.test"

    def test_generate_routing_key(self) -> None:
        """Test routing key generation."""

        class TestEvent(IntegrationEvent):
            pass

        with patch.object(
            TestEvent, "__module__", "app.modules.catalog.domain.events"
        ):
            event = TestEvent()
            assert event.routing_key == "app.catalog.test"

    def test_from_domain_event(self) -> None:
        """Test creating integration event from domain event."""
        domain_event = TestDomainEvent(id=uuid4(), name="test_product", value=42)

        integration_event = IntegrationEvent.from_domain_event(
            domain_event, additional_key="additional_value"
        )

        assert integration_event.event_type == "test_domain"
        assert integration_event.source_module == "tests"
        assert "domain_event_type" in integration_event.data
        assert "domain_event_module" in integration_event.data
        assert integration_event.data["name"] == "test_product"
        assert integration_event.data["value"] == 42
        assert integration_event.data["additional_key"] == "additional_value"

    def test_extract_event_name_from_class(self) -> None:
        """Test event name extraction from class name."""
        assert (
            IntegrationEvent._extract_event_name_from_class("ProductCreatedEvent")
            == "product_created"
        )
        assert (
            IntegrationEvent._extract_event_name_from_class("OrderCancelledCommand")
            == "order_cancelled"
        )
        assert IntegrationEvent._extract_event_name_from_class("UserQuery") == "user"
        assert (
            IntegrationEvent._extract_event_name_from_class("SimpleName")
            == "simple_name"
        )

    def test_extract_module_from_path(self) -> None:
        """Test module extraction from path."""
        assert (
            IntegrationEvent._extract_module_from_path(
                "app.modules.catalog.domain.events"
            )
            == "catalog"
        )
        assert (
            IntegrationEvent._extract_module_from_path(
                "app.modules.basket.domain.events"
            )
            == "basket"
        )
        assert (
            IntegrationEvent._extract_module_from_path("app.core.messaging") == "core"
        )
        assert IntegrationEvent._extract_module_from_path("unknown.path") == "unknown"


class TestModuleIntegrationEvent:
    """Test ModuleIntegrationEvent class."""

    def test_module_integration_event(self) -> None:
        """Test ModuleIntegrationEvent with specific module."""
        event = ModuleIntegrationEvent(module_name="test_module")

        assert event.source_module == "test_module"
        assert event.topic == "app.messaging.module_integration"
        assert event.routing_key == "app.test_module.module_integration"

    def test_catalog_integration_event(self) -> None:
        """Test CatalogIntegrationEvent."""
        event = CatalogIntegrationEvent()

        assert event.source_module == "catalog"
        assert event.topic == "app.messaging.catalog_integration"
        assert event.routing_key == "app.catalog.catalog_integration"

    def test_basket_integration_event(self) -> None:
        """Test BasketIntegrationEvent."""
        event = BasketIntegrationEvent()

        assert event.source_module == "basket"
        assert event.topic == "app.messaging.basket_integration"
        assert event.routing_key == "app.basket.basket_integration"

    def test_ordering_integration_event(self) -> None:
        """Test OrderingIntegrationEvent."""
        event = OrderingIntegrationEvent()

        assert event.source_module == "ordering"
        assert event.topic == "app.messaging.ordering_integration"
        assert event.routing_key == "app.ordering.ordering_integration"


class TestOutboxMessage:
    """Test OutboxMessage class."""

    def test_outbox_message_default_values(self) -> None:
        """Test OutboxMessage with default values."""
        message = OutboxMessage(type="test_type", content="test_content")

        assert isinstance(message.id, UUID)
        assert message.type == "test_type"
        assert message.content == "test_content"
        assert message.routing_key == ""
        assert message.topic == ""
        assert isinstance(message.created_on, datetime)
        assert message.processed_on is None
        assert message.error is None

    def test_outbox_message_custom_values(self) -> None:
        """Test OutboxMessage with custom values."""
        custom_id = uuid4()
        custom_date = datetime.now(UTC)
        processed_date = datetime.now(UTC)

        message = OutboxMessage(
            id=custom_id,
            type="custom_type",
            content="custom_content",
            routing_key="custom.routing.key",
            topic="custom.topic",
            created_on=custom_date,
            processed_on=processed_date,
            error="test_error",
        )

        assert message.id == custom_id
        assert message.type == "custom_type"
        assert message.content == "custom_content"
        assert message.routing_key == "custom.routing.key"
        assert message.topic == "custom.topic"
        assert message.created_on == custom_date
        assert message.processed_on == processed_date
        assert message.error == "test_error"


class TestFastStreamEventPublisher:
    """Test FastStreamEventPublisher class."""

    def test_faststream_event_publisher_init(self) -> None:
        """Test FastStreamEventPublisher initialization."""
        mock_broker = MagicMock(spec=RabbitBroker)
        publisher = FastStreamEventPublisher(mock_broker)

        assert publisher.broker == mock_broker

    @pytest.mark.asyncio
    async def test_publish_with_routing_key(self) -> None:
        """Test publishing with routing key."""
        mock_broker = AsyncMock(spec=RabbitBroker)
        publisher = FastStreamEventPublisher(mock_broker)

        event = IntegrationEvent(
            event_type="test_event", routing_key="test.routing.key", topic="test.topic"
        )

        await publisher.publish(event, routing_key="custom.routing.key")

        mock_broker.publish.assert_called_once()
        call_args = mock_broker.publish.call_args
        assert call_args[1]["routing_key"] == "custom.routing.key"

    @pytest.mark.asyncio
    async def test_publish_without_routing_key(self) -> None:
        """Test publishing without routing key."""
        mock_broker = AsyncMock(spec=RabbitBroker)
        publisher = FastStreamEventPublisher(mock_broker)

        event = IntegrationEvent(
            event_type="test_event", routing_key="test.routing.key", topic="test.topic"
        )

        await publisher.publish(event)

        mock_broker.publish.assert_called_once()
        call_args = mock_broker.publish.call_args
        assert call_args[1]["routing_key"] == "test.routing.key"

    @pytest.mark.asyncio
    async def test_publish_message_structure(self) -> None:
        """Test published message structure."""
        mock_broker = AsyncMock(spec=RabbitBroker)
        publisher = FastStreamEventPublisher(mock_broker)

        event = IntegrationEvent(
            event_type="test_event",
            routing_key="test.routing.key",
            topic="test.topic",
            source_module="test_module",
            data={"key": "value"},
        )

        await publisher.publish(event)

        mock_broker.publish.assert_called_once()
        call_args = mock_broker.publish.call_args
        message = call_args[0][0]

        assert message["event_type"] == "test_event"
        assert message["routing_key"] == "test.routing.key"
        assert message["topic"] == "test.topic"
        assert message["source_module"] == "test_module"
        assert message["data"] == {"key": "value"}
        assert "_metadata" in message
        assert "published_at" in message["_metadata"]


class TestFastStreamEventHandler:
    """Test FastStreamEventHandler class."""

    def test_faststream_event_handler_init(self) -> None:
        """Test FastStreamEventHandler initialization."""
        handler_func = MagicMock()
        handler = FastStreamEventHandler(handler_func)

        assert handler.handler_func == handler_func

    @pytest.mark.asyncio
    async def test_handle_event(self) -> None:
        """Test handling event with FastStreamEventHandler."""
        handler_func = AsyncMock()
        handler = FastStreamEventHandler(handler_func)

        event = IntegrationEvent(event_type="test_event")

        await handler.handle(event)

        handler_func.assert_called_once_with(event)


class TestEventBus:
    """Test EventBus class."""

    def test_event_bus_init(self) -> None:
        """Test EventBus initialization."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        assert event_bus.broker == mock_broker
        assert isinstance(event_bus.app, FastStream)
        assert event_bus.handlers == {}
        assert event_bus.routing_patterns == {}

    def test_register_handler(self) -> None:
        """Test registering a handler."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        mock_handler = MagicMock(spec=IIntegrationEventHandler)

        event_bus.register_handler("test_event", mock_handler, "test.pattern")

        assert event_bus.handlers["test_event"] == mock_handler
        assert event_bus.routing_patterns["test_event"] == "test.pattern"

    def test_register_handler_without_pattern(self) -> None:
        """Test registering a handler without routing pattern."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        mock_handler = MagicMock(spec=IIntegrationEventHandler)

        event_bus.register_handler("test_event", mock_handler)

        assert event_bus.handlers["test_event"] == mock_handler
        assert "test_event" not in event_bus.routing_patterns

    def test_register_module_handlers(self) -> None:
        """Test registering multiple handlers for a module."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        mock_handler1 = MagicMock(spec=IIntegrationEventHandler)
        mock_handler2 = MagicMock(spec=IIntegrationEventHandler)

        handlers: dict[str, IIntegrationEventHandler] = {
            "event1": mock_handler1,
            "event2": mock_handler2,
        }

        event_bus.register_module_handlers("test_module", handlers)

        assert event_bus.handlers["event1"] == mock_handler1
        assert event_bus.handlers["event2"] == mock_handler2
        assert event_bus.routing_patterns["event1"] == "app.test_module.event1"
        assert event_bus.routing_patterns["event2"] == "app.test_module.event2"

    @pytest.mark.asyncio
    async def test_publish_event(self) -> None:
        """Test publishing an event."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        event = IntegrationEvent(event_type="test_event")

        with patch(
            "app.core.messaging.integration_event.FastStreamEventPublisher"
        ) as mock_publisher_class:
            mock_publisher = AsyncMock()
            mock_publisher_class.return_value = mock_publisher

            await event_bus.publish(event, "custom.routing.key")

            mock_publisher_class.assert_called_once_with(mock_broker)
            mock_publisher.publish.assert_called_once_with(event, "custom.routing.key")

    @pytest.mark.asyncio
    async def test_publish_from_domain_event(self) -> None:
        """Test publishing from domain event."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        domain_event = TestDomainEvent(id=uuid4(), name="test", value=42)

        with patch.object(event_bus, "publish") as mock_publish:
            await event_bus.publish_from_domain_event(domain_event, extra="data")

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            integration_event = call_args[0][0]

            assert isinstance(integration_event, IntegrationEvent)
            assert integration_event.data["name"] == "test"
            assert integration_event.data["value"] == 42
            assert integration_event.data["extra"] == "data"

    @pytest.mark.asyncio
    async def test_handle_event_success(self) -> None:
        """Test handling an event successfully."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        mock_handler = AsyncMock(spec=IIntegrationEventHandler)
        event_bus.register_handler("test_event", mock_handler)

        event = IntegrationEvent(event_type="test_event")

        await event_bus.handle_event(event)

        mock_handler.handle.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_handle_event_no_handler(self) -> None:
        """Test handling an event with no registered handler."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        event = IntegrationEvent(event_type="unknown_event")

        with pytest.raises(ValueError, match="No handler registered for event type"):
            await event_bus.handle_event(event)

    def test_get_app(self) -> None:
        """Test getting FastStream app."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        app = event_bus.get_app()

        assert isinstance(app, FastStream)

    def test_get_routing_key_for_event(self) -> None:
        """Test getting routing key for event."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        # Test with registered pattern
        event_bus.register_handler("test_event", MagicMock(), "custom.pattern")
        assert event_bus.get_routing_key_for_event("test_event") == "custom.pattern"

        # Test with default pattern
        assert (
            event_bus.get_routing_key_for_event("unknown_event")
            == "app.*.unknown_event"
        )


class TestMessagingIntegration:
    """Integration tests for messaging functionality."""

    @pytest.mark.asyncio
    async def test_complete_event_flow(self) -> None:
        """Test complete event publishing and handling flow."""
        mock_broker = MagicMock(spec=RabbitBroker)
        event_bus = EventBus(mock_broker)

        # Create a test handler
        handled_events = []

        async def test_handler(event: IntegrationEvent) -> None:
            handled_events.append(event)

        handler = FastStreamEventHandler(test_handler)
        event_bus.register_handler("test_event", handler)

        # Create and publish event
        event = IntegrationEvent(event_type="test_event", data={"key": "value"})

        with patch(
            "app.core.messaging.integration_event.FastStreamEventPublisher"
        ) as mock_publisher_class:
            mock_publisher = AsyncMock()
            mock_publisher_class.return_value = mock_publisher

            await event_bus.publish(event)
            await event_bus.handle_event(event)

            # Verify publishing
            mock_publisher.publish.assert_called_once()

            # Verify handling
            assert len(handled_events) == 1
            assert handled_events[0] == event

    def test_event_serialization(self) -> None:
        """Test event serialization and deserialization."""
        event = IntegrationEvent(
            event_type="test_event", data={"nested": {"key": "value"}}
        )

        # Test model_dump
        event_dict = event.model_dump()
        assert event_dict["event_type"] == "test_event"
        assert event_dict["data"]["nested"]["key"] == "value"

        # Test model_dump_json
        event_json = event.model_dump_json()
        assert "test_event" in event_json
        assert "nested" in event_json

    def test_outbox_message_processing(self) -> None:
        """Test outbox message processing workflow."""
        # Create outbox message
        message = OutboxMessage(
            type="test_event",
            content='{"event_type": "test_event", "data": {"key": "value"}}',
            routing_key="test.routing.key",
        )

        assert message.processed_on is None
        assert message.error is None

        # Simulate processing
        message.processed_on = datetime.now(UTC)

        assert message.processed_on is not None

        # Simulate error
        message.error = "Processing failed"

        assert message.error == "Processing failed"

    def test_module_specific_events(self) -> None:
        """Test module-specific integration events."""
        catalog_event = CatalogIntegrationEvent(data={"product_id": "123"})
        basket_event = BasketIntegrationEvent(data={"basket_id": "456"})
        ordering_event = OrderingIntegrationEvent(data={"order_id": "789"})

        assert catalog_event.source_module == "catalog"
        assert basket_event.source_module == "basket"
        assert ordering_event.source_module == "ordering"

        assert "catalog" in catalog_event.topic
        assert "basket" in basket_event.topic
        assert "ordering" in ordering_event.topic
