"""Tests for exchange resolver and basket outbox worker lifecycle."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.core.messaging.exchange_resolver import get_exchange_for_event_type
from app.modules.basket.workers.outbox_publisher_worker import BasketOutboxPublisherWorker


class TestExchangeResolver:
    def test_product_event_maps_to_catalog_exchange(self) -> None:
        assert get_exchange_for_event_type("product.deleted.v1") == "catalog.events"

    def test_basket_event_maps_to_basket_exchange(self) -> None:
        assert get_exchange_for_event_type("basket_checkout_integration") == "basket.events"

    def test_unknown_event_returns_none(self) -> None:
        assert get_exchange_for_event_type("unknown.event") is None


@pytest.mark.asyncio
async def test_worker_start_and_stop() -> None:
    bus = MagicMock()
    worker = BasketOutboxPublisherWorker(message_bus=bus, poll_interval=0.01)

    await worker.start()
    assert worker.is_running is True
    await worker.stop()
    assert worker.is_running is False
