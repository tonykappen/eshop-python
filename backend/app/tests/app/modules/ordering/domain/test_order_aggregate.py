"""Tests for Order aggregate."""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.modules.ordering.domain.entities.order.order import Order
from app.modules.ordering.domain.value_objects.address import Address
from app.modules.ordering.domain.value_objects.payment import Payment


def _address() -> Address:
    return Address.of(
        first_name="Jane",
        last_name="Doe",
        email_address="jane@example.com",
        address_line="123 Main St",
        country="US",
        state="CA",
        zip_code="90210",
    )


def _payment() -> Payment:
    return Payment.of(
        card_name="Jane Doe",
        card_number="4111111111111111",
        expiration="12/30",
        cvv="123",
        payment_method=1,
    )


class TestOrderAggregate:
    def test_create_emits_domain_event(self) -> None:
        order_id = uuid4()
        order = Order.create(
            id=order_id,
            customer_id=uuid4(),
            order_name="Order-1",
            shipping_address=_address(),
            billing_address=_address(),
            payment=_payment(),
        )
        assert order.id == order_id
        assert len(order.domain_events) == 1

    def test_add_item_and_total_price(self) -> None:
        order = Order.create(
            id=uuid4(),
            customer_id=uuid4(),
            order_name="Order-2",
            shipping_address=_address(),
            billing_address=_address(),
            payment=_payment(),
        )
        product_id = uuid4()
        order.add(product_id, quantity=2, price=Decimal("10.00"))
        assert order.total_price == Decimal("20.00")

        order.add(product_id, quantity=1, price=Decimal("10.00"))
        assert order.total_price == Decimal("30.00")

    def test_add_rejects_invalid_quantity(self) -> None:
        order = Order.create(
            id=uuid4(),
            customer_id=uuid4(),
            order_name="Order-3",
            shipping_address=_address(),
            billing_address=_address(),
            payment=_payment(),
        )
        with pytest.raises(ValueError, match="Quantity"):
            order.add(uuid4(), quantity=0, price=Decimal("1.00"))

    def test_remove_item(self) -> None:
        order = Order.create(
            id=uuid4(),
            customer_id=uuid4(),
            order_name="Order-4",
            shipping_address=_address(),
            billing_address=_address(),
            payment=_payment(),
        )
        product_id = uuid4()
        order.add(product_id, quantity=1, price=Decimal("5.00"))
        order.remove(product_id)
        assert order.items == []
