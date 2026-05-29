"""Tests for messaging exchange resolver."""

import json

from app.core.messaging import exchange_resolver


class TestExchangeResolverMappings:
    def test_default_product_mapping(self) -> None:
        assert exchange_resolver.get_exchange_for_event_type("product.price_changed.v1") == "catalog.events"

    def test_default_order_mapping(self) -> None:
        assert exchange_resolver.get_exchange_for_event_type("order.created.v1") == "ordering.events"

    def test_custom_mapping_from_env(self, monkeypatch) -> None:
        mappings = {"custom.event": "custom.events"}
        monkeypatch.setenv("EVENT_EXCHANGE_MAPPINGS", json.dumps(mappings))
        exchange_resolver._get_custom_exchange_mappings.cache_clear() if hasattr(exchange_resolver._get_custom_exchange_mappings, "cache_clear") else None
        assert exchange_resolver.get_exchange_for_event_type("custom.event") == "custom.events"
