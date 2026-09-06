"""Tests for BasketCheckoutIntegrationEventHandler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.core.messaging.integration_event import IntegrationEvent
from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import (
    BasketCheckoutIntegrationEvent, BasketCheckoutItem)
from app.modules.ordering.application.integration_event_handlers.basket.basket_checkout_integration_event_handler import \
    BasketCheckoutIntegrationEventHandler


class TestBasketCheckoutIntegrationEventHandler:
    """Test BasketCheckoutIntegrationEventHandler."""

    @pytest.fixture
    def sample_basket_checkout_event(self) -> BasketCheckoutIntegrationEvent:
        """Create sample basket checkout event for testing."""
        customer_id = uuid4()
        product_id = uuid4()

        items = [
            BasketCheckoutItem(
                product_id=product_id,
                quantity=2,
                price=Decimal("99.99"),
            )
        ]

        return BasketCheckoutIntegrationEvent(
            user_name="testuser",
            customer_id=customer_id,
            total_price=Decimal("199.98"),
            items=items,
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
            card_name="John Doe",
            card_number="1234567890123456",
            expiration="12/25",
            cvv="123",
            payment_method=1,
        )

    @pytest.mark.asyncio
    async def test_handle_success(
        self, sample_basket_checkout_event: BasketCheckoutIntegrationEvent
    ) -> None:
        """Test successful event handling."""
        mock_mediator = AsyncMock()
        handler = BasketCheckoutIntegrationEventHandler(mediator=mock_mediator)

        # Mock mediator.send to return a result
        mock_result = MagicMock()
        mock_result.id = uuid4()
        mock_mediator.send.return_value = mock_result

        await handler.handle(sample_basket_checkout_event)

        # Verify mediator.send was called with CreateOrderCommand
        assert mock_mediator.send.called
        call_args = mock_mediator.send.call_args
        assert call_args is not None
        command = call_args[0][0]
        assert hasattr(command, "order")
        assert command.order.customer_id == sample_basket_checkout_event.customer_id
        assert command.order.order_name == sample_basket_checkout_event.user_name
        assert len(command.order.items) == len(sample_basket_checkout_event.items)

    @pytest.mark.asyncio
    async def test_handle_wrong_event_type(self) -> None:
        """Test that wrong event type is ignored."""
        mock_mediator = AsyncMock()
        handler = BasketCheckoutIntegrationEventHandler(mediator=mock_mediator)

        # Create a different event type
        wrong_event = MagicMock(spec=IntegrationEvent)

        await handler.handle(wrong_event)

        # Verify mediator.send was not called
        assert not mock_mediator.send.called

    @pytest.mark.asyncio
    async def test_handle_event_mapping(
        self, sample_basket_checkout_event: BasketCheckoutIntegrationEvent
    ) -> None:
        """Test that event is correctly mapped to CreateOrderCommand."""
        mock_mediator = AsyncMock()
        handler = BasketCheckoutIntegrationEventHandler(mediator=mock_mediator)

        mock_result = MagicMock()
        mock_result.id = uuid4()
        mock_mediator.send.return_value = mock_result

        await handler.handle(sample_basket_checkout_event)

        # Verify the mapping
        call_args = mock_mediator.send.call_args
        command = call_args[0][0]

        # Check address mapping
        assert (
            command.order.shipping_address.first_name
            == sample_basket_checkout_event.first_name
        )
        assert (
            command.order.shipping_address.last_name
            == sample_basket_checkout_event.last_name
        )
        assert (
            command.order.shipping_address.email_address
            == sample_basket_checkout_event.email_address
        )
        assert (
            command.order.billing_address.first_name
            == sample_basket_checkout_event.first_name
        )

        # Check payment mapping
        assert command.order.payment.card_name == sample_basket_checkout_event.card_name
        assert (
            command.order.payment.card_number
            == sample_basket_checkout_event.card_number
        )
        assert (
            command.order.payment.expiration == sample_basket_checkout_event.expiration
        )

        # Check items mapping
        assert len(command.order.items) == len(sample_basket_checkout_event.items)
        assert (
            command.order.items[0].product_id
            == sample_basket_checkout_event.items[0].product_id
        )
        assert (
            command.order.items[0].quantity
            == sample_basket_checkout_event.items[0].quantity
        )
        assert (
            command.order.items[0].price == sample_basket_checkout_event.items[0].price
        )

    @pytest.mark.asyncio
    async def test_handle_exception_propagates(
        self, sample_basket_checkout_event: BasketCheckoutIntegrationEvent
    ) -> None:
        """Test that exceptions during handling are propagated."""
        mock_mediator = AsyncMock()
        handler = BasketCheckoutIntegrationEventHandler(mediator=mock_mediator)

        # Mock mediator to raise exception
        mock_mediator.send.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            await handler.handle(sample_basket_checkout_event)
        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_multiple_items(
        self, sample_basket_checkout_event: BasketCheckoutIntegrationEvent
    ) -> None:
        """Test event handling with multiple items."""
        mock_mediator = AsyncMock()
        handler = BasketCheckoutIntegrationEventHandler(mediator=mock_mediator)

        # Add more items
        product_id2 = uuid4()
        item2 = BasketCheckoutItem(
            product_id=product_id2,
            quantity=1,
            price=Decimal("49.99"),
        )
        sample_basket_checkout_event.items.append(item2)

        mock_result = MagicMock()
        mock_result.id = uuid4()
        mock_mediator.send.return_value = mock_result

        await handler.handle(sample_basket_checkout_event)

        # Verify all items are mapped
        call_args = mock_mediator.send.call_args
        command = call_args[0][0]
        assert len(command.order.items) == 2
