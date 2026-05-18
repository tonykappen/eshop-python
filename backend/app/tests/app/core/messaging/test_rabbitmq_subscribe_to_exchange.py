"""Tests for RabbitMQMessageBus.subscribe_to_exchange.

The .NET reference (berkayzaimdev/eShopModularMonolith) creates a durable
queue per MassTransit consumer endpoint and binds it to the message-type
exchange. This test pins the Python equivalent: ``subscribe_to_exchange``
must declare the named queue durably, bind it to the requested exchange
with the supplied routing key, and start consuming.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.core.messaging.bus import RabbitMQMessageBus


@pytest.mark.asyncio
async def test_subscribe_to_exchange_declares_queue_and_binds_routing_key() -> None:
    """Queue must be declared durable and bound to the exchange/routing key."""
    bus = RabbitMQMessageBus("amqp://guest:guest@localhost:5672/")

    exchange_obj = MagicMock(name="exchange_obj")
    queue_obj = MagicMock(name="queue_obj")
    queue_obj.bind = AsyncMock()
    queue_obj.consume = AsyncMock()

    channel = MagicMock(name="channel")
    channel.declare_exchange = AsyncMock(return_value=exchange_obj)
    channel.declare_queue = AsyncMock(return_value=queue_obj)

    connection = MagicMock(name="connection")
    connection.is_closed = False

    bus._connection = connection
    bus._channel = channel

    handler = AsyncMock()

    await bus.subscribe_to_exchange(
        exchange="basket.events",
        routing_key="basket_checkout_integration",
        queue_name="basket-checkout-queue",
        handler=handler,
    )

    # Exchange lookup is attempted passively first (matches publish path).
    channel.declare_exchange.assert_awaited()
    first_call = channel.declare_exchange.await_args_list[0]
    assert first_call.args[0] == "basket.events"
    assert first_call.kwargs.get("passive") is True

    # Durable queue is declared with the consumer-owned name.
    channel.declare_queue.assert_awaited_once_with(
        "basket-checkout-queue", durable=True
    )

    # Queue is bound to the exchange with the routing key.
    queue_obj.bind.assert_awaited_once_with(
        exchange_obj, routing_key="basket_checkout_integration"
    )

    # Consumer is started.
    queue_obj.consume.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_to_exchange_falls_back_to_active_declare_when_passive_fails() -> (
    None
):
    """When passive declare raises, we fall back to declaring the exchange ourselves."""
    bus = RabbitMQMessageBus("amqp://guest:guest@localhost:5672/")

    exchange_obj = MagicMock(name="exchange_obj")
    queue_obj = MagicMock(name="queue_obj")
    queue_obj.bind = AsyncMock()
    queue_obj.consume = AsyncMock()

    channel = MagicMock(name="channel")
    channel.declare_exchange = AsyncMock(
        side_effect=[RuntimeError("not found"), exchange_obj]
    )
    channel.declare_queue = AsyncMock(return_value=queue_obj)

    connection = MagicMock(name="connection")
    connection.is_closed = False

    bus._connection = connection
    bus._channel = channel

    await bus.subscribe_to_exchange(
        exchange="basket.events",
        routing_key="basket_checkout_integration",
        queue_name="basket-checkout-queue",
        handler=AsyncMock(),
    )

    assert channel.declare_exchange.await_count == 2
    second_call = channel.declare_exchange.await_args_list[1]
    assert second_call.args[0] == "basket.events"
    assert second_call.kwargs.get("passive") is not True
    queue_obj.bind.assert_awaited_once_with(
        exchange_obj, routing_key="basket_checkout_integration"
    )
