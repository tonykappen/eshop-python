"""Catalog messaging integration tests (outbox contracts + message bus)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.core.messaging.bus import (
    InMemoryMessageBus,
    RabbitMQMessageBus,
    build_message_envelope,
)
from app.modules.catalog.contracts.products.integration_events.v1.product_deleted_integration_event import (
    ProductDeletedIntegrationEvent,
)
from app.modules.catalog.contracts.products.integration_events.v1.product_price_changed_integration_event import (
    ProductPriceChangedIntegrationEventV1,
)


class TestCatalogIntegrationEventContracts:
    """Integration event contract shapes used by catalog outbox publishing."""

    def test_product_price_changed_event_structure(self) -> None:
        product_id = uuid4()
        event = ProductPriceChangedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="SKU-001",
            old_price_amount=99.99,
            new_price_amount=89.99,
        )

        assert event.event_type == "product.price_changed.v1"
        assert event.product_id == product_id
        assert event.old_price_amount == 99.99
        assert event.new_price_amount == 89.99
        assert event.price_change_percentage == pytest.approx(-10.01, rel=0.01)

        payload = event.to_dict()
        assert payload["product_id"] == str(product_id)
        assert payload["event_type"] == "product.price_changed.v1"

    def test_product_deleted_event_structure(self) -> None:
        product_id = uuid4()
        event = ProductDeletedIntegrationEvent.create(
            product_id=product_id,
            product_name="Removed Product",
            product_sku="SKU-DEL",
        )

        assert event.event_type == "product.deleted.v1"
        assert event.product_id == product_id
        payload = event.to_dict()
        assert payload["product_name"] == "Removed Product"


class TestCatalogMessageEnvelope:
    """Envelope wrapping used when publishing catalog integration events."""

    def test_build_message_envelope_uses_event_type(self) -> None:
        event = ProductPriceChangedIntegrationEventV1.create(
            product_id=uuid4(),
            product_name="Widget",
            product_sku="W-1",
            old_price_amount=10.0,
            new_price_amount=12.0,
        )
        envelope = build_message_envelope(
            event,
            topic="app.catalog.product_price_changed_integration",
            exchange="catalog.events",
        )

        assert envelope["routing_key"] == "app.catalog.product_price_changed_integration"
        assert envelope["exchange"] == "catalog.events"
        assert envelope["message_type"] == "product.price_changed.v1"
        assert envelope["payload"]["product_name"] == "Widget"


@pytest.mark.asyncio
async def test_in_memory_bus_delivers_catalog_event_to_handler() -> None:
    bus = InMemoryMessageBus()
    received: list[dict] = []

    async def handler(message: dict) -> None:
        received.append(message)

    await bus.subscribe("app.catalog.product_deleted_integration", handler)
    payload = {"product_id": str(uuid4()), "event_type": "product.deleted.v1"}
    await bus.publish(payload, topic="app.catalog.product_deleted_integration")

    assert len(received) == 1
    assert received[0]["event_type"] == "product.deleted.v1"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rabbitmq_publish_catalog_event_with_mock_channel() -> None:
    """Publish path against mocked RabbitMQ channel (no live broker required)."""
    bus = RabbitMQMessageBus("amqp://guest:guest@localhost:5672/")

    exchange_obj = MagicMock()
    exchange_obj.publish = AsyncMock()

    channel = MagicMock()
    channel.declare_exchange = AsyncMock(return_value=exchange_obj)
    channel.is_closed = False

    connection = MagicMock()
    connection.is_closed = False

    bus._connection = connection
    bus._channel = channel

    event = ProductPriceChangedIntegrationEventV1.create(
        product_id=uuid4(),
        product_name="Catalog Item",
        product_sku="CAT-1",
        old_price_amount=50.0,
        new_price_amount=45.0,
    )

    await bus.publish(
        event.to_dict(),
        topic="app.catalog.product_price_changed_integration",
        exchange="catalog.events",
    )

    exchange_obj.publish.assert_awaited_once()
    call_kwargs = exchange_obj.publish.await_args.kwargs
    assert call_kwargs["routing_key"] == "app.catalog.product_price_changed_integration"
