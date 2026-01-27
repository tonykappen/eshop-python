"""Tests for Order aggregate and value objects."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.ordering.domain.entities.order.order import Order
from app.modules.ordering.domain.value_objects import Address, Payment


class TestOrderAggregate:
    """Test Order aggregate."""

    @pytest.fixture
    def sample_address(self) -> Address:
        """Create sample address for testing."""
        return Address.of(
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
        )

    @pytest.fixture
    def sample_payment(self) -> Payment:
        """Create sample payment for testing."""
        return Payment.of(
            card_name="John Doe",
            card_number="1234567890123456",
            expiration="12/25",
            cvv="123",
            payment_method=1,
        )

    def test_order_creation(
        self, sample_address: Address, sample_payment: Payment
    ) -> None:
        """Test order creation."""
        order_id = uuid4()
        customer_id = uuid4()

        order = Order.create(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=sample_address,
            billing_address=sample_address,
            payment=sample_payment,
        )

        assert order.id == order_id
        assert order.customer_id == customer_id
        assert order.order_name == "Test Order"
        assert order.shipping_address == sample_address
        assert order.billing_address == sample_address
        assert order.payment == sample_payment
        assert len(order.items) == 0
        assert order.total_price == Decimal("0")

    def test_order_add_item(
        self, sample_address: Address, sample_payment: Payment
    ) -> None:
        """Test adding item to order."""
        order_id = uuid4()
        customer_id = uuid4()
        product_id = uuid4()

        order = Order.create(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=sample_address,
            billing_address=sample_address,
            payment=sample_payment,
        )

        order.add(product_id=product_id, quantity=2, price=Decimal("99.99"))

        assert len(order.items) == 1
        assert order.items[0].product_id == product_id
        assert order.items[0].quantity == 2
        assert order.items[0].price == Decimal("99.99")
        assert order.total_price == Decimal("199.98")

    def test_order_add_multiple_items(
        self, sample_address: Address, sample_payment: Payment
    ) -> None:
        """Test adding multiple items to order."""
        order_id = uuid4()
        customer_id = uuid4()
        product_id1 = uuid4()
        product_id2 = uuid4()

        order = Order.create(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=sample_address,
            billing_address=sample_address,
            payment=sample_payment,
        )

        order.add(product_id=product_id1, quantity=2, price=Decimal("99.99"))
        order.add(product_id=product_id2, quantity=1, price=Decimal("49.99"))

        assert len(order.items) == 2
        assert order.total_price == Decimal("249.97")

    def test_order_add_duplicate_item_increments_quantity(
        self, sample_address: Address, sample_payment: Payment
    ) -> None:
        """Test adding duplicate item increments quantity."""
        order_id = uuid4()
        customer_id = uuid4()
        product_id = uuid4()

        order = Order.create(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=sample_address,
            billing_address=sample_address,
            payment=sample_payment,
        )

        order.add(product_id=product_id, quantity=2, price=Decimal("99.99"))
        order.add(product_id=product_id, quantity=1, price=Decimal("99.99"))

        assert len(order.items) == 1
        assert order.items[0].quantity == 3
        assert order.total_price == Decimal("299.97")

    def test_order_remove_item(
        self, sample_address: Address, sample_payment: Payment
    ) -> None:
        """Test removing item from order."""
        order_id = uuid4()
        customer_id = uuid4()
        product_id = uuid4()

        order = Order.create(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=sample_address,
            billing_address=sample_address,
            payment=sample_payment,
        )

        order.add(product_id=product_id, quantity=2, price=Decimal("99.99"))
        assert len(order.items) == 1

        order.remove(product_id=product_id)
        assert len(order.items) == 0
        assert order.total_price == Decimal("0")

    def test_order_remove_nonexistent_item(
        self, sample_address: Address, sample_payment: Payment
    ) -> None:
        """Test removing nonexistent item does nothing."""
        order_id = uuid4()
        customer_id = uuid4()
        product_id = uuid4()
        other_product_id = uuid4()

        order = Order.create(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=sample_address,
            billing_address=sample_address,
            payment=sample_payment,
        )

        order.add(product_id=product_id, quantity=2, price=Decimal("99.99"))
        assert len(order.items) == 1

        order.remove(product_id=other_product_id)
        assert len(order.items) == 1

    def test_order_add_item_invalid_quantity(
        self, sample_address: Address, sample_payment: Payment
    ) -> None:
        """Test adding item with invalid quantity raises error."""
        order_id = uuid4()
        customer_id = uuid4()
        product_id = uuid4()

        order = Order.create(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=sample_address,
            billing_address=sample_address,
            payment=sample_payment,
        )

        with pytest.raises(ValueError) as exc_info:
            order.add(product_id=product_id, quantity=0, price=Decimal("99.99"))
        assert "Quantity must be greater than 0" in str(exc_info.value)

    def test_order_add_item_invalid_price(
        self, sample_address: Address, sample_payment: Payment
    ) -> None:
        """Test adding item with invalid price raises error."""
        order_id = uuid4()
        customer_id = uuid4()
        product_id = uuid4()

        order = Order.create(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=sample_address,
            billing_address=sample_address,
            payment=sample_payment,
        )

        with pytest.raises(ValueError) as exc_info:
            order.add(product_id=product_id, quantity=2, price=Decimal("0"))
        assert "Price must be greater than 0" in str(exc_info.value)


class TestAddressValueObject:
    """Test Address value object."""

    def test_address_creation(self) -> None:
        """Test address creation."""
        address = Address.of(
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
        )

        assert address.first_name == "John"
        assert address.last_name == "Doe"
        assert address.email_address == "john@example.com"
        assert address.address_line == "123 Main St"
        assert address.country == "USA"
        assert address.state == "CA"
        assert address.zip_code == "12345"

    def test_address_empty_email_raises_error(self) -> None:
        """Test that empty email raises error."""
        with pytest.raises(ValueError) as exc_info:
            Address.of(
                first_name="John",
                last_name="Doe",
                email_address="",
                address_line="123 Main St",
                country="USA",
                state="CA",
                zip_code="12345",
            )
        assert "Email address is required" in str(exc_info.value)

    def test_address_empty_address_line_raises_error(self) -> None:
        """Test that empty address line raises error."""
        with pytest.raises(ValueError) as exc_info:
            Address.of(
                first_name="John",
                last_name="Doe",
                email_address="john@example.com",
                address_line="",
                country="USA",
                state="CA",
                zip_code="12345",
            )
        assert "Address line is required" in str(exc_info.value)


class TestPaymentValueObject:
    """Test Payment value object."""

    def test_payment_creation(self) -> None:
        """Test payment creation."""
        payment = Payment.of(
            card_name="John Doe",
            card_number="1234567890123456",
            expiration="12/25",
            cvv="123",
            payment_method=1,
        )

        assert payment.card_name == "John Doe"
        assert payment.card_number == "1234567890123456"
        assert payment.expiration == "12/25"
        assert payment.cvv == "123"
        assert payment.payment_method == 1

    def test_payment_empty_card_name_raises_error(self) -> None:
        """Test that empty card name raises error."""
        with pytest.raises(ValueError) as exc_info:
            Payment.of(
                card_name="",
                card_number="1234567890123456",
                expiration="12/25",
                cvv="123",
                payment_method=1,
            )
        assert "Card name is required" in str(exc_info.value)

    def test_payment_empty_card_number_raises_error(self) -> None:
        """Test that empty card number raises error."""
        with pytest.raises(ValueError) as exc_info:
            Payment.of(
                card_name="John Doe",
                card_number="",
                expiration="12/25",
                cvv="123",
                payment_method=1,
            )
        assert "Card number is required" in str(exc_info.value)

    def test_payment_empty_cvv_raises_error(self) -> None:
        """Test that empty CVV raises error."""
        with pytest.raises(ValueError) as exc_info:
            Payment.of(
                card_name="John Doe",
                card_number="1234567890123456",
                expiration="12/25",
                cvv="",
                payment_method=1,
            )
        assert "CVV is required" in str(exc_info.value)

    def test_payment_cvv_too_long_raises_error(self) -> None:
        """Test that CVV too long raises error."""
        with pytest.raises(ValueError) as exc_info:
            Payment.of(
                card_name="John Doe",
                card_number="1234567890123456",
                expiration="12/25",
                cvv="1234",
                payment_method=1,
            )
        assert "CVV length cannot be greater than 3" in str(exc_info.value)
