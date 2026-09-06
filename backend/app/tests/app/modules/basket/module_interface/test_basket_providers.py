"""Tests for basket DI providers."""

from app.core.messaging.bus import RabbitMQMessageBus
from app.modules.basket.module_interface.di.basket import basket_providers


class TestBasketProviders:
    def test_get_basket_message_bus_singleton(self) -> None:
        basket_providers.get_basket_message_bus.cache_clear()
        bus1 = basket_providers.get_basket_message_bus()
        bus2 = basket_providers.get_basket_message_bus()
        assert isinstance(bus1, RabbitMQMessageBus)
        assert bus1 is bus2

    def test_create_basket_handler_context_factory_returns_callable(self) -> None:
        factory = basket_providers.create_basket_handler_context_factory()
        assert callable(factory)
