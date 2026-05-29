"""Tests for message bus helpers and in-memory bus."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.core.messaging.bus import (
    InMemoryMessageBus,
    RabbitMQMessageBus,
    _message_to_json_serializable,
    build_message_envelope,
)
from pydantic import BaseModel


class SampleEvent(BaseModel):
    event_type: str = "sample.event"
    value: int = 1


class TestMessageSerialization:
    def test_message_to_json_serializable_primitives(self) -> None:
        assert _message_to_json_serializable(None) is None
        assert _message_to_json_serializable(True) is True
        assert _message_to_json_serializable(42) == 42
        assert _message_to_json_serializable({"a": 1}) == {"a": 1}

    def test_message_to_json_serializable_pydantic(self) -> None:
        event = SampleEvent(value=7)
        result = _message_to_json_serializable(event)
        assert result["value"] == 7

    def test_build_message_envelope(self) -> None:
        envelope = build_message_envelope(
            {"id": str(uuid4())},
            topic="test.topic",
            exchange="test.events",
        )
        assert envelope["routing_key"] == "test.topic"
        assert envelope["exchange"] == "test.events"
        assert "message_id" in envelope
        assert "occurred_at" in envelope


@pytest.mark.asyncio
async def test_in_memory_bus_subscribe_publish_unsubscribe() -> None:
    bus = InMemoryMessageBus()
    calls: list[str] = []

    async def handler(message: str) -> None:
        calls.append(message)

    await bus.subscribe("orders.created", handler)
    await bus.publish("hello", topic="orders.created")
    assert calls == ["hello"]
    assert len(bus.get_message_history()) == 1

    await bus.unsubscribe("orders.created", handler)
    await bus.publish("ignored", topic="orders.created")
    assert calls == ["hello"]

    bus.clear_history()
    assert bus.get_message_history() == []


@pytest.mark.asyncio
async def test_in_memory_bus_handler_with_handle_method() -> None:
    bus = InMemoryMessageBus()

    class Handler:
        async def handle(self, message: dict) -> None:
            self.last = message

    h = Handler()
    await bus.subscribe("evt", h)
    await bus.publish({"ok": True}, topic="evt")
    assert h.last == {"ok": True}


@pytest.mark.asyncio
async def test_in_memory_bus_handler_error_is_logged() -> None:
    bus = InMemoryMessageBus()

    async def bad_handler(_message: object) -> None:
        raise RuntimeError("handler failed")

    await bus.subscribe("fail", bad_handler)
    await bus.publish("x", topic="fail")


@pytest.mark.asyncio
async def test_rabbitmq_publish_without_connection_attempts_connect() -> None:
    bus = RabbitMQMessageBus("amqp://guest:guest@localhost:5672/")
    with pytest.raises(Exception, match="connect"):
        with patch.object(bus, "connect", side_effect=ConnectionError("cannot connect")):
            await bus.publish({"x": 1}, topic="test", exchange="catalog.events")


@pytest.mark.asyncio
async def test_rabbitmq_disconnect_closes_channel_and_connection() -> None:
    bus = RabbitMQMessageBus("amqp://guest:guest@localhost:5672/")

    channel = MagicMock()
    channel.is_closed = False
    channel.close = AsyncMock()

    connection = MagicMock()
    connection.close = AsyncMock()

    bus._channel = channel
    bus._connection = connection

    await bus.disconnect()
    channel.close.assert_awaited_once()
    connection.close.assert_awaited_once()
    assert bus._channel is None
    assert bus._connection is None
