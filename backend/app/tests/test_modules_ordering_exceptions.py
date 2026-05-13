"""Tests for ordering module exceptions."""

from uuid import uuid4

from app.core.exceptions.common_exceptions import NotFoundError
from app.modules.ordering.domain.exceptions import (
    InventoryReservationError,
    OrderCancellationError,
    OrderCreationError,
    OrderItemNotFoundError,
    OrderNotFoundError,
    OrderStatusTransitionError,
    OrderUpdateError,
    OrderValidationError,
    PaymentProcessingError,
)


class TestOrderNotFoundError:
    """Test OrderNotFoundError exception."""

    def test_order_not_found_error_initialization(self) -> None:
        """Test OrderNotFoundError initialization."""
        order_id = uuid4()
        error = OrderNotFoundError(order_id)

        assert error.order_id == order_id
        assert str(order_id) in str(error)
        assert "Order" in str(error)

    def test_order_not_found_error_inheritance(self) -> None:
        """Test that OrderNotFoundError inherits from NotFoundError."""
        order_id = uuid4()
        error = OrderNotFoundError(order_id)

        assert isinstance(error, NotFoundError)
        assert isinstance(error, Exception)

    def test_order_not_found_error_message(self) -> None:
        """Test OrderNotFoundError message format."""
        order_id = uuid4()
        error = OrderNotFoundError(order_id)

        error_message = str(error)
        assert "Order" in error_message
        assert str(order_id) in error_message

    def test_order_not_found_error_attributes(self) -> None:
        """Test OrderNotFoundError attributes."""
        order_id = uuid4()
        error = OrderNotFoundError(order_id)

        assert hasattr(error, "order_id")
        assert error.order_id == order_id
        # Note: name and key are not stored as attributes, only used in message


class TestOrderItemNotFoundError:
    """Test OrderItemNotFoundError exception."""

    def test_order_item_not_found_error_initialization(self) -> None:
        """Test OrderItemNotFoundError initialization."""
        item_id = uuid4()
        error = OrderItemNotFoundError(item_id)

        assert error.item_id == item_id
        assert str(item_id) in str(error)
        assert "OrderItem" in str(error)

    def test_order_item_not_found_error_inheritance(self) -> None:
        """Test that OrderItemNotFoundError inherits from NotFoundError."""
        item_id = uuid4()
        error = OrderItemNotFoundError(item_id)

        assert isinstance(error, NotFoundError)
        assert isinstance(error, Exception)

    def test_order_item_not_found_error_message(self) -> None:
        """Test OrderItemNotFoundError message format."""
        item_id = uuid4()
        error = OrderItemNotFoundError(item_id)

        error_message = str(error)
        assert "OrderItem" in error_message
        assert str(item_id) in error_message

    def test_order_item_not_found_error_attributes(self) -> None:
        """Test OrderItemNotFoundError attributes."""
        item_id = uuid4()
        error = OrderItemNotFoundError(item_id)

        assert hasattr(error, "item_id")
        assert error.item_id == item_id
        # Note: name and key are not stored as attributes, only used in message


class TestOrderValidationError:
    """Test OrderValidationError exception."""

    def test_order_validation_error_initialization(self) -> None:
        """Test OrderValidationError initialization."""
        message = "Invalid order data"
        error = OrderValidationError(message)

        assert error.message == message
        assert error.field is None
        assert str(error) == message

    def test_order_validation_error_with_field(self) -> None:
        """Test OrderValidationError initialization with field."""
        message = "Invalid quantity"
        field = "quantity"
        error = OrderValidationError(message, field)

        assert error.message == message
        assert error.field == field
        assert str(error) == message

    def test_order_validation_error_inheritance(self) -> None:
        """Test that OrderValidationError inherits from Exception."""
        error = OrderValidationError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_order_validation_error_attributes(self) -> None:
        """Test OrderValidationError attributes."""
        message = "Test validation error"
        field = "test_field"
        error = OrderValidationError(message, field)

        assert hasattr(error, "message")
        assert hasattr(error, "field")
        assert error.message == message
        assert error.field == field


class TestOrderCreationError:
    """Test OrderCreationError exception."""

    def test_order_creation_error_initialization(self) -> None:
        """Test OrderCreationError initialization."""
        message = "Failed to create order"
        error = OrderCreationError(message)

        assert error.message == message
        assert error.details is None
        assert str(error) == message

    def test_order_creation_error_with_details(self) -> None:
        """Test OrderCreationError initialization with details."""
        message = "Failed to create order"
        details = "Database connection failed"
        error = OrderCreationError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == message

    def test_order_creation_error_inheritance(self) -> None:
        """Test that OrderCreationError inherits from Exception."""
        error = OrderCreationError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_order_creation_error_attributes(self) -> None:
        """Test OrderCreationError attributes."""
        message = "Test creation error"
        details = "Test details"
        error = OrderCreationError(message, details)

        assert hasattr(error, "message")
        assert hasattr(error, "details")
        assert error.message == message
        assert error.details == details


class TestOrderUpdateError:
    """Test OrderUpdateError exception."""

    def test_order_update_error_initialization(self) -> None:
        """Test OrderUpdateError initialization."""
        message = "Failed to update order"
        error = OrderUpdateError(message)

        assert error.message == message
        assert error.details is None
        assert str(error) == message

    def test_order_update_error_with_details(self) -> None:
        """Test OrderUpdateError initialization with details."""
        message = "Failed to update order"
        details = "Concurrency conflict"
        error = OrderUpdateError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == message

    def test_order_update_error_inheritance(self) -> None:
        """Test that OrderUpdateError inherits from Exception."""
        error = OrderUpdateError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_order_update_error_attributes(self) -> None:
        """Test OrderUpdateError attributes."""
        message = "Test update error"
        details = "Test details"
        error = OrderUpdateError(message, details)

        assert hasattr(error, "message")
        assert hasattr(error, "details")
        assert error.message == message
        assert error.details == details


class TestOrderCancellationError:
    """Test OrderCancellationError exception."""

    def test_order_cancellation_error_initialization(self) -> None:
        """Test OrderCancellationError initialization."""
        message = "Failed to cancel order"
        error = OrderCancellationError(message)

        assert error.message == message
        assert error.details is None
        assert str(error) == message

    def test_order_cancellation_error_with_details(self) -> None:
        """Test OrderCancellationError initialization with details."""
        message = "Failed to cancel order"
        details = "Order already shipped"
        error = OrderCancellationError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == message

    def test_order_cancellation_error_inheritance(self) -> None:
        """Test that OrderCancellationError inherits from Exception."""
        error = OrderCancellationError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_order_cancellation_error_attributes(self) -> None:
        """Test OrderCancellationError attributes."""
        message = "Test cancellation error"
        details = "Test details"
        error = OrderCancellationError(message, details)

        assert hasattr(error, "message")
        assert hasattr(error, "details")
        assert error.message == message
        assert error.details == details


class TestOrderStatusTransitionError:
    """Test OrderStatusTransitionError exception."""

    def test_order_status_transition_error_initialization(self) -> None:
        """Test OrderStatusTransitionError initialization."""
        current_status = "Pending"
        target_status = "Shipped"
        order_id = uuid4()

        error = OrderStatusTransitionError(current_status, target_status, order_id)

        assert error.current_status == current_status
        assert error.target_status == target_status
        assert error.order_id == order_id

    def test_order_status_transition_error_message(self) -> None:
        """Test OrderStatusTransitionError message format."""
        current_status = "Pending"
        target_status = "Shipped"
        order_id = uuid4()

        error = OrderStatusTransitionError(current_status, target_status, order_id)

        error_message = str(error)
        assert current_status in error_message
        assert target_status in error_message
        assert str(order_id) in error_message
        assert "Invalid status transition" in error_message

    def test_order_status_transition_error_inheritance(self) -> None:
        """Test that OrderStatusTransitionError inherits from Exception."""
        error = OrderStatusTransitionError("Pending", "Shipped", uuid4())

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_order_status_transition_error_attributes(self) -> None:
        """Test OrderStatusTransitionError attributes."""
        current_status = "Pending"
        target_status = "Shipped"
        order_id = uuid4()

        error = OrderStatusTransitionError(current_status, target_status, order_id)

        assert hasattr(error, "current_status")
        assert hasattr(error, "target_status")
        assert hasattr(error, "order_id")
        assert error.current_status == current_status
        assert error.target_status == target_status
        assert error.order_id == order_id

    def test_order_status_transition_error_with_empty_statuses(self) -> None:
        """Test OrderStatusTransitionError with empty status strings."""
        current_status = ""
        target_status = ""
        order_id = uuid4()

        error = OrderStatusTransitionError(current_status, target_status, order_id)

        assert error.current_status == ""
        assert error.target_status == ""
        assert error.order_id == order_id
        assert str(order_id) in str(error)


class TestPaymentProcessingError:
    """Test PaymentProcessingError exception."""

    def test_payment_processing_error_initialization(self) -> None:
        """Test PaymentProcessingError initialization."""
        message = "Payment processing failed"
        error = PaymentProcessingError(message)

        assert error.message == message
        assert error.payment_id is None
        assert error.details is None
        assert str(error) == message

    def test_payment_processing_error_with_payment_id(self) -> None:
        """Test PaymentProcessingError initialization with payment ID."""
        message = "Payment processing failed"
        payment_id = uuid4()
        error = PaymentProcessingError(message, payment_id)

        assert error.message == message
        assert error.payment_id == payment_id
        assert error.details is None
        assert str(error) == message

    def test_payment_processing_error_with_details(self) -> None:
        """Test PaymentProcessingError initialization with details."""
        message = "Payment processing failed"
        payment_id = uuid4()
        details = "Card declined"
        error = PaymentProcessingError(message, payment_id, details)

        assert error.message == message
        assert error.payment_id == payment_id
        assert error.details == details
        assert str(error) == message

    def test_payment_processing_error_inheritance(self) -> None:
        """Test that PaymentProcessingError inherits from Exception."""
        error = PaymentProcessingError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_payment_processing_error_attributes(self) -> None:
        """Test PaymentProcessingError attributes."""
        message = "Test payment error"
        payment_id = uuid4()
        details = "Test details"
        error = PaymentProcessingError(message, payment_id, details)

        assert hasattr(error, "message")
        assert hasattr(error, "payment_id")
        assert hasattr(error, "details")
        assert error.message == message
        assert error.payment_id == payment_id
        assert error.details == details


class TestInventoryReservationError:
    """Test InventoryReservationError exception."""

    def test_inventory_reservation_error_initialization(self) -> None:
        """Test InventoryReservationError initialization."""
        message = "Inventory reservation failed"
        error = InventoryReservationError(message)

        assert error.message == message
        assert error.product_id is None
        assert error.details is None
        assert str(error) == message

    def test_inventory_reservation_error_with_product_id(self) -> None:
        """Test InventoryReservationError initialization with product ID."""
        message = "Inventory reservation failed"
        product_id = uuid4()
        error = InventoryReservationError(message, product_id)

        assert error.message == message
        assert error.product_id == product_id
        assert error.details is None
        assert str(error) == message

    def test_inventory_reservation_error_with_details(self) -> None:
        """Test InventoryReservationError initialization with details."""
        message = "Inventory reservation failed"
        product_id = uuid4()
        details = "Insufficient stock"
        error = InventoryReservationError(message, product_id, details)

        assert error.message == message
        assert error.product_id == product_id
        assert error.details == details
        assert str(error) == message

    def test_inventory_reservation_error_inheritance(self) -> None:
        """Test that InventoryReservationError inherits from Exception."""
        error = InventoryReservationError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_inventory_reservation_error_attributes(self) -> None:
        """Test InventoryReservationError attributes."""
        message = "Test inventory error"
        product_id = uuid4()
        details = "Test details"
        error = InventoryReservationError(message, product_id, details)

        assert hasattr(error, "message")
        assert hasattr(error, "product_id")
        assert hasattr(error, "details")
        assert error.message == message
        assert error.product_id == product_id
        assert error.details == details


class TestOrderingExceptionsIntegration:
    """Integration tests for ordering exceptions."""

    def test_exception_hierarchy(self) -> None:
        """Test the exception hierarchy."""
        # Test NotFoundError hierarchy
        order_id = uuid4()
        item_id = uuid4()

        order_error = OrderNotFoundError(order_id)
        item_error = OrderItemNotFoundError(item_id)

        assert isinstance(order_error, NotFoundError)
        assert isinstance(item_error, NotFoundError)
        assert isinstance(order_error, Exception)
        assert isinstance(item_error, Exception)

    def test_exception_message_consistency(self) -> None:
        """Test that exception messages are consistent."""
        order_id = uuid4()
        item_id = uuid4()
        payment_id = uuid4()
        product_id = uuid4()

        order_error = OrderNotFoundError(order_id)
        item_error = OrderItemNotFoundError(item_id)
        status_error = OrderStatusTransitionError("Pending", "Shipped", order_id)
        payment_error = PaymentProcessingError("Payment failed", payment_id)
        inventory_error = InventoryReservationError("Reservation failed", product_id)

        # All should have meaningful messages
        assert len(str(order_error)) > 0
        assert len(str(item_error)) > 0
        assert len(str(status_error)) > 0
        assert len(str(payment_error)) > 0
        assert len(str(inventory_error)) > 0

        # Messages should contain relevant IDs
        assert str(order_id) in str(order_error)
        assert str(item_id) in str(item_error)
        assert str(order_id) in str(status_error)
        # Note: PaymentProcessingError doesn't include payment_id in message, only stores it as attribute
        # Note: InventoryReservationError doesn't include product_id in message, only stores it as attribute
        assert inventory_error.product_id == product_id

    def test_exception_attributes_consistency(self) -> None:
        """Test that exception attributes are consistent."""
        order_id = uuid4()
        item_id = uuid4()
        payment_id = uuid4()
        product_id = uuid4()

        order_error = OrderNotFoundError(order_id)
        item_error = OrderItemNotFoundError(item_id)
        validation_error = OrderValidationError("Test", "field")
        creation_error = OrderCreationError("Test", "details")
        update_error = OrderUpdateError("Test", "details")
        cancellation_error = OrderCancellationError("Test", "details")
        status_error = OrderStatusTransitionError("Pending", "Shipped", order_id)
        payment_error = PaymentProcessingError("Test", payment_id, "details")
        inventory_error = InventoryReservationError("Test", product_id, "details")

        # All should have the expected attributes
        assert hasattr(order_error, "order_id")
        assert hasattr(item_error, "item_id")
        assert hasattr(validation_error, "message")
        assert hasattr(validation_error, "field")
        assert hasattr(creation_error, "message")
        assert hasattr(creation_error, "details")
        assert hasattr(update_error, "message")
        assert hasattr(update_error, "details")
        assert hasattr(cancellation_error, "message")
        assert hasattr(cancellation_error, "details")
        assert hasattr(status_error, "current_status")
        assert hasattr(status_error, "target_status")
        assert hasattr(status_error, "order_id")
        assert hasattr(payment_error, "message")
        assert hasattr(payment_error, "payment_id")
        assert hasattr(payment_error, "details")
        assert hasattr(inventory_error, "message")
        assert hasattr(inventory_error, "product_id")
        assert hasattr(inventory_error, "details")

    def test_exception_usage_patterns(self) -> None:
        """Test common usage patterns for ordering exceptions."""
        # Simulate a typical error handling scenario
        try:
            order_id = uuid4()
            raise OrderNotFoundError(order_id)
        except OrderNotFoundError as e:
            assert e.order_id == order_id
            assert "Order" in str(e)

        try:
            message = "Invalid order data"
            field = "quantity"
            raise OrderValidationError(message, field)
        except OrderValidationError as e:
            assert e.message == message
            assert e.field == field

        try:
            current_status = "Pending"
            target_status = "Shipped"
            order_id = uuid4()
            raise OrderStatusTransitionError(current_status, target_status, order_id)
        except OrderStatusTransitionError as e:
            assert e.current_status == current_status
            assert e.target_status == target_status
            assert e.order_id == order_id
            assert "Invalid status transition" in str(e)

        try:
            payment_id = uuid4()
            raise PaymentProcessingError("Payment failed", payment_id, "Card declined")
        except PaymentProcessingError as e:
            assert e.payment_id == payment_id
            assert e.details == "Card declined"
            assert "Payment failed" in str(e)

        try:
            product_id = uuid4()
            raise InventoryReservationError(
                "Reservation failed", product_id, "Out of stock"
            )
        except InventoryReservationError as e:
            assert e.product_id == product_id
            assert e.details == "Out of stock"
            assert "Reservation failed" in str(e)

    def test_exception_edge_cases(self) -> None:
        """Test edge cases for ordering exceptions."""
        # Test with empty strings
        validation_error = OrderValidationError("", "")
        assert validation_error.message == ""
        assert validation_error.field == ""

        # Test with None values
        creation_error = OrderCreationError("Test", None)
        assert creation_error.message == "Test"
        assert creation_error.details is None

        # Test with large UUIDs
        large_order_id = uuid4()
        order_error = OrderNotFoundError(large_order_id)
        assert order_error.order_id == large_order_id
        assert str(large_order_id) in str(order_error)

        # Test status transition with special characters
        status_error = OrderStatusTransitionError("Pending!", "Shipped@", uuid4())
        assert status_error.current_status == "Pending!"
        assert status_error.target_status == "Shipped@"
        assert "Pending!" in str(status_error)
        assert "Shipped@" in str(status_error)
