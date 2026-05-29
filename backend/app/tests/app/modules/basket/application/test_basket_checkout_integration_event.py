"""Tests for basket integration event contracts."""

from decimal import Decimal
from uuid import uuid4

from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import (
    BasketCheckoutIntegrationEvent,
    BasketCheckoutItem,
)


class TestBasketCheckoutIntegrationEvent:
    def test_event_serializes_checkout_payload(self) -> None:
        item = BasketCheckoutItem(
            product_id=uuid4(), quantity=2, price=Decimal("9.99")
        )
        event = BasketCheckoutIntegrationEvent(
            user_name="testuser",
            customer_id=uuid4(),
            total_price=Decimal("19.98"),
            items=[item],
            first_name="Jane",
            last_name="Doe",
            email_address="jane@example.com",
            address_line="123 Main",
            country="US",
            state="CA",
            zip_code="90210",
            card_name="Jane Doe",
            card_number="4111111111111111",
            expiration="12/30",
            cvv="123",
            payment_method=1,
        )
        payload = event.model_dump(mode="json")
        assert payload["user_name"] == "testuser"
        assert len(payload["items"]) == 1
