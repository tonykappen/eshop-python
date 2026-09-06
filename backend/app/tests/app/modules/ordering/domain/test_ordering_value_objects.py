"""Tests for ordering domain value objects."""

import pytest
from app.modules.ordering.domain.value_objects.address import Address
from app.modules.ordering.domain.value_objects.payment import Payment


class TestAddress:
    def test_of_creates_valid_address(self) -> None:
        address = Address.of(
            first_name="Jane",
            last_name="Doe",
            email_address="jane@example.com",
            address_line="123 Main St",
            country="US",
            state="CA",
            zip_code="90210",
        )
        assert address.first_name == "Jane"
        assert address.email_address == "jane@example.com"

    def test_of_rejects_empty_email(self) -> None:
        with pytest.raises(ValueError, match="Email address"):
            Address.of(
                first_name="Jane",
                last_name="Doe",
                email_address="  ",
                address_line="123 Main St",
                country="US",
                state="CA",
                zip_code="90210",
            )

    def test_of_rejects_empty_address_line(self) -> None:
        with pytest.raises(ValueError, match="Address line"):
            Address.of(
                first_name="Jane",
                last_name="Doe",
                email_address="jane@example.com",
                address_line="",
                country="US",
                state="CA",
                zip_code="90210",
            )


class TestPayment:
    def test_of_creates_valid_payment(self) -> None:
        payment = Payment.of(
            card_name="Jane Doe",
            card_number="4111111111111111",
            expiration="12/30",
            cvv="123",
            payment_method=1,
        )
        assert payment.card_number == "4111111111111111"
        assert payment.cvv == "123"

    def test_of_rejects_long_cvv(self) -> None:
        with pytest.raises(ValueError, match="CVV length"):
            Payment.of(
                card_name="Jane Doe",
                card_number="4111111111111111",
                expiration="12/30",
                cvv="1234",
                payment_method=1,
            )

    def test_of_rejects_empty_card_number(self) -> None:
        with pytest.raises(ValueError, match="Card number"):
            Payment.of(
                card_name="Jane Doe",
                card_number="",
                expiration="12/30",
                cvv="123",
                payment_method=1,
            )
