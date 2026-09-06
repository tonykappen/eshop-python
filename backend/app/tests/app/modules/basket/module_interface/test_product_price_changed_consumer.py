"""Tests for basket catalog price-change RabbitMQ consumer adapter."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.modules.basket.module_interface.product_price_changed_subscription import (
    CATALOG_EVENTS_EXCHANGE,
    PRODUCT_PRICE_CHANGED_QUEUE,
    coerce_product_price_changed_payload,
    subscribe_product_price_changed_consumer,
)
from app.modules.catalog.contracts.products.integration_events.v1.product_price_changed_integration_event import \
    ProductPriceChangedIntegrationEventV1


def test_coerce_product_price_changed_payload_parses_uuid_strings() -> None:
    event_id = uuid4()
    product_id = uuid4()
    payload = {
        "event_id": str(event_id),
        "event_type": "product.price_changed.v1",
        "event_version": "1.0",
        "occurred_at": datetime.utcnow().isoformat(),
        "source": "catalog-service",
        "product_id": str(product_id),
        "product_name": "Samsung Galaxy",
        "product_sku": "SG-001",
        "old_price_amount": 100.0,
        "new_price_amount": 120.0,
        "price_currency": "USD",
        "price_change_percentage": 20.0,
        "metadata": {},
    }

    coerced = coerce_product_price_changed_payload(payload)

    assert coerced["event_id"] == event_id
    assert coerced["product_id"] == product_id
    model = ProductPriceChangedIntegrationEventV1(**coerced)
    assert model.product_name == "Samsung Galaxy"
    assert model.new_price_amount == 120.0


@pytest.mark.asyncio
async def test_subscribe_basket_handlers_declares_catalog_exchange_binding() -> None:
    """Consumer wiring binds basket queue to catalog.events with routing key."""
    mock_bus = MagicMock()
    mock_bus._connection = object()
    mock_bus.connect = AsyncMock()
    mock_bus.subscribe_to_exchange = AsyncMock()

    captured_handler = None

    async def capture_subscribe(**kwargs):
        nonlocal captured_handler
        captured_handler = kwargs.get("handler")

    mock_bus.subscribe_to_exchange.side_effect = capture_subscribe

    with (
        patch(
            "app.modules.basket.module_interface.di.basket.basket_providers.get_basket_message_bus",
            return_value=mock_bus,
        ),
        patch(
            "app.core.mediator.fastapi_integration.get_mediator",
            return_value=MagicMock(),
        ),
        patch(
            "app.modules.basket.application.integration_event_handlers.products.product_price_changed_integration_event_handler.ProductPriceChangedIntegrationEventHandler"
        ) as handler_cls,
    ):
        handler_instance = MagicMock()
        handler_instance.handle = AsyncMock()
        handler_cls.return_value = handler_instance

        await subscribe_product_price_changed_consumer()

    mock_bus.subscribe_to_exchange.assert_awaited_once()
    call_kwargs = mock_bus.subscribe_to_exchange.await_args.kwargs
    assert call_kwargs["exchange"] == CATALOG_EVENTS_EXCHANGE
    assert call_kwargs["routing_key"] == "product.price_changed.v1"
    assert call_kwargs["queue_name"] == PRODUCT_PRICE_CHANGED_QUEUE
    assert captured_handler is not None

    product_id = uuid4()
    event_id = uuid4()
    await captured_handler(
        {
            "event_id": str(event_id),
            "event_type": "product.price_changed.v1",
            "event_version": "1.0",
            "occurred_at": datetime.utcnow().isoformat(),
            "source": "catalog-service",
            "product_id": str(product_id),
            "product_name": "MacBook",
            "product_sku": "MB-001",
            "old_price_amount": 1000.0,
            "new_price_amount": 1100.0,
            "price_currency": "USD",
            "price_change_percentage": 10.0,
            "metadata": {},
        }
    )

    handler_instance.handle.assert_awaited_once()
    event_arg = handler_instance.handle.await_args.args[0]
    assert isinstance(event_arg, ProductPriceChangedIntegrationEventV1)
    assert event_arg.product_id == product_id
