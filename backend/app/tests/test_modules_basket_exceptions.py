"""Tests for basket module exceptions."""

from uuid import uuid4

from app.core.exceptions.common_exceptions import NotFoundError
from app.modules.basket.domain.exceptions import (BasketCreationError,
                                                  BasketDeletionError,
                                                  BasketItemNotFoundError,
                                                  BasketNotFoundError,
                                                  BasketUpdateError,
                                                  BasketValidationError,
                                                  InsufficientStockError)


class TestBasketNotFoundError:
    """Test BasketNotFoundError exception."""

    def test_basket_not_found_error_initialization(self) -> None:
        """Test BasketNotFoundError initialization."""
        basket_id = uuid4()
        error = BasketNotFoundError(basket_id)

        assert error.basket_id == basket_id
        assert str(basket_id) in str(error)
        assert "Basket" in str(error)

    def test_basket_not_found_error_inheritance(self) -> None:
        """Test that BasketNotFoundError inherits from NotFoundError."""
        basket_id = uuid4()
        error = BasketNotFoundError(basket_id)

        assert isinstance(error, NotFoundError)
        assert isinstance(error, Exception)

    def test_basket_not_found_error_message(self) -> None:
        """Test BasketNotFoundError message format."""
        basket_id = uuid4()
        error = BasketNotFoundError(basket_id)

        error_message = str(error)
        assert "Basket" in error_message
        assert str(basket_id) in error_message

    def test_basket_not_found_error_attributes(self) -> None:
        """Test BasketNotFoundError attributes."""
        basket_id = uuid4()
        error = BasketNotFoundError(basket_id)

        assert hasattr(error, "basket_id")
        assert error.basket_id == basket_id
        # Note: name and key are not stored as attributes, only used in message


class TestBasketItemNotFoundError:
    """Test BasketItemNotFoundError exception."""

    def test_basket_item_not_found_error_initialization(self) -> None:
        """Test BasketItemNotFoundError initialization."""
        item_id = uuid4()
        error = BasketItemNotFoundError(item_id)

        assert error.item_id == item_id
        assert str(item_id) in str(error)
        assert "BasketItem" in str(error)

    def test_basket_item_not_found_error_inheritance(self) -> None:
        """Test that BasketItemNotFoundError inherits from NotFoundError."""
        item_id = uuid4()
        error = BasketItemNotFoundError(item_id)

        assert isinstance(error, NotFoundError)
        assert isinstance(error, Exception)

    def test_basket_item_not_found_error_message(self) -> None:
        """Test BasketItemNotFoundError message format."""
        item_id = uuid4()
        error = BasketItemNotFoundError(item_id)

        error_message = str(error)
        assert "BasketItem" in error_message
        assert str(item_id) in error_message

    def test_basket_item_not_found_error_attributes(self) -> None:
        """Test BasketItemNotFoundError attributes."""
        item_id = uuid4()
        error = BasketItemNotFoundError(item_id)

        assert hasattr(error, "item_id")
        assert error.item_id == item_id
        # Note: name and key are not stored as attributes, only used in message


class TestBasketValidationError:
    """Test BasketValidationError exception."""

    def test_basket_validation_error_initialization(self) -> None:
        """Test BasketValidationError initialization."""
        message = "Invalid basket data"
        error = BasketValidationError(message)

        assert error.message == message
        assert error.field is None
        assert str(error) == message

    def test_basket_validation_error_with_field(self) -> None:
        """Test BasketValidationError initialization with field."""
        message = "Invalid quantity"
        field = "quantity"
        error = BasketValidationError(message, field)

        assert error.message == message
        assert error.field == field
        assert str(error) == message

    def test_basket_validation_error_inheritance(self) -> None:
        """Test that BasketValidationError inherits from Exception."""
        error = BasketValidationError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_basket_validation_error_attributes(self) -> None:
        """Test BasketValidationError attributes."""
        message = "Test validation error"
        field = "test_field"
        error = BasketValidationError(message, field)

        assert hasattr(error, "message")
        assert hasattr(error, "field")
        assert error.message == message
        assert error.field == field


class TestBasketCreationError:
    """Test BasketCreationError exception."""

    def test_basket_creation_error_initialization(self) -> None:
        """Test BasketCreationError initialization."""
        message = "Failed to create basket"
        error = BasketCreationError(message)

        assert error.message == message
        assert error.details is None
        assert str(error) == message

    def test_basket_creation_error_with_details(self) -> None:
        """Test BasketCreationError initialization with details."""
        message = "Failed to create basket"
        details = "Database connection failed"
        error = BasketCreationError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == message

    def test_basket_creation_error_inheritance(self) -> None:
        """Test that BasketCreationError inherits from Exception."""
        error = BasketCreationError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_basket_creation_error_attributes(self) -> None:
        """Test BasketCreationError attributes."""
        message = "Test creation error"
        details = "Test details"
        error = BasketCreationError(message, details)

        assert hasattr(error, "message")
        assert hasattr(error, "details")
        assert error.message == message
        assert error.details == details


class TestBasketUpdateError:
    """Test BasketUpdateError exception."""

    def test_basket_update_error_initialization(self) -> None:
        """Test BasketUpdateError initialization."""
        message = "Failed to update basket"
        error = BasketUpdateError(message)

        assert error.message == message
        assert error.details is None
        assert str(error) == message

    def test_basket_update_error_with_details(self) -> None:
        """Test BasketUpdateError initialization with details."""
        message = "Failed to update basket"
        details = "Concurrency conflict"
        error = BasketUpdateError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == message

    def test_basket_update_error_inheritance(self) -> None:
        """Test that BasketUpdateError inherits from Exception."""
        error = BasketUpdateError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_basket_update_error_attributes(self) -> None:
        """Test BasketUpdateError attributes."""
        message = "Test update error"
        details = "Test details"
        error = BasketUpdateError(message, details)

        assert hasattr(error, "message")
        assert hasattr(error, "details")
        assert error.message == message
        assert error.details == details


class TestBasketDeletionError:
    """Test BasketDeletionError exception."""

    def test_basket_deletion_error_initialization(self) -> None:
        """Test BasketDeletionError initialization."""
        message = "Failed to delete basket"
        error = BasketDeletionError(message)

        assert error.message == message
        assert error.details is None
        assert str(error) == message

    def test_basket_deletion_error_with_details(self) -> None:
        """Test BasketDeletionError initialization with details."""
        message = "Failed to delete basket"
        details = "Basket has active items"
        error = BasketDeletionError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == message

    def test_basket_deletion_error_inheritance(self) -> None:
        """Test that BasketDeletionError inherits from Exception."""
        error = BasketDeletionError("Test message")

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_basket_deletion_error_attributes(self) -> None:
        """Test BasketDeletionError attributes."""
        message = "Test deletion error"
        details = "Test details"
        error = BasketDeletionError(message, details)

        assert hasattr(error, "message")
        assert hasattr(error, "details")
        assert error.message == message
        assert error.details == details


class TestInsufficientStockError:
    """Test InsufficientStockError exception."""

    def test_insufficient_stock_error_initialization(self) -> None:
        """Test InsufficientStockError initialization."""
        product_id = uuid4()
        requested_quantity = 10
        available_quantity = 5

        error = InsufficientStockError(
            product_id, requested_quantity, available_quantity
        )

        assert error.product_id == product_id
        assert error.requested_quantity == requested_quantity
        assert error.available_quantity == available_quantity

    def test_insufficient_stock_error_message(self) -> None:
        """Test InsufficientStockError message format."""
        product_id = uuid4()
        requested_quantity = 10
        available_quantity = 5

        error = InsufficientStockError(
            product_id, requested_quantity, available_quantity
        )

        error_message = str(error)
        assert str(product_id) in error_message
        assert str(requested_quantity) in error_message
        assert str(available_quantity) in error_message
        assert "Insufficient stock" in error_message

    def test_insufficient_stock_error_inheritance(self) -> None:
        """Test that InsufficientStockError inherits from Exception."""
        product_id = uuid4()
        error = InsufficientStockError(product_id, 10, 5)

        assert isinstance(error, Exception)
        assert not isinstance(error, NotFoundError)

    def test_insufficient_stock_error_attributes(self) -> None:
        """Test InsufficientStockError attributes."""
        product_id = uuid4()
        requested_quantity = 10
        available_quantity = 5

        error = InsufficientStockError(
            product_id, requested_quantity, available_quantity
        )

        assert hasattr(error, "product_id")
        assert hasattr(error, "requested_quantity")
        assert hasattr(error, "available_quantity")
        assert error.product_id == product_id
        assert error.requested_quantity == requested_quantity
        assert error.available_quantity == available_quantity

    def test_insufficient_stock_error_zero_quantities(self) -> None:
        """Test InsufficientStockError with zero quantities."""
        product_id = uuid4()
        requested_quantity = 0
        available_quantity = 0

        error = InsufficientStockError(
            product_id, requested_quantity, available_quantity
        )

        assert error.requested_quantity == 0
        assert error.available_quantity == 0
        assert str(product_id) in str(error)

    def test_insufficient_stock_error_large_quantities(self) -> None:
        """Test InsufficientStockError with large quantities."""
        product_id = uuid4()
        requested_quantity = 1000000
        available_quantity = 999999

        error = InsufficientStockError(
            product_id, requested_quantity, available_quantity
        )

        assert error.requested_quantity == 1000000
        assert error.available_quantity == 999999
        assert str(1000000) in str(error)
        assert str(999999) in str(error)


class TestBasketExceptionsIntegration:
    """Integration tests for basket exceptions."""

    def test_exception_hierarchy(self) -> None:
        """Test the exception hierarchy."""
        # Test NotFoundError hierarchy
        basket_id = uuid4()
        item_id = uuid4()

        basket_error = BasketNotFoundError(basket_id)
        item_error = BasketItemNotFoundError(item_id)

        assert isinstance(basket_error, NotFoundError)
        assert isinstance(item_error, NotFoundError)
        assert isinstance(basket_error, Exception)
        assert isinstance(item_error, Exception)

    def test_exception_message_consistency(self) -> None:
        """Test that exception messages are consistent."""
        basket_id = uuid4()
        item_id = uuid4()
        product_id = uuid4()

        basket_error = BasketNotFoundError(basket_id)
        item_error = BasketItemNotFoundError(item_id)
        stock_error = InsufficientStockError(product_id, 10, 5)

        # All should have meaningful messages
        assert len(str(basket_error)) > 0
        assert len(str(item_error)) > 0
        assert len(str(stock_error)) > 0

        # Messages should contain relevant IDs
        assert str(basket_id) in str(basket_error)
        assert str(item_id) in str(item_error)
        assert str(product_id) in str(stock_error)

    def test_exception_attributes_consistency(self) -> None:
        """Test that exception attributes are consistent."""
        basket_id = uuid4()
        item_id = uuid4()
        product_id = uuid4()

        basket_error = BasketNotFoundError(basket_id)
        item_error = BasketItemNotFoundError(item_id)
        validation_error = BasketValidationError("Test", "field")
        creation_error = BasketCreationError("Test", "details")
        update_error = BasketUpdateError("Test", "details")
        deletion_error = BasketDeletionError("Test", "details")
        stock_error = InsufficientStockError(product_id, 10, 5)

        # All should have the expected attributes
        assert hasattr(basket_error, "basket_id")
        assert hasattr(item_error, "item_id")
        assert hasattr(validation_error, "message")
        assert hasattr(validation_error, "field")
        assert hasattr(creation_error, "message")
        assert hasattr(creation_error, "details")
        assert hasattr(update_error, "message")
        assert hasattr(update_error, "details")
        assert hasattr(deletion_error, "message")
        assert hasattr(deletion_error, "details")
        assert hasattr(stock_error, "product_id")
        assert hasattr(stock_error, "requested_quantity")
        assert hasattr(stock_error, "available_quantity")

    def test_exception_usage_patterns(self) -> None:
        """Test common usage patterns for basket exceptions."""
        # Simulate a typical error handling scenario
        try:
            basket_id = uuid4()
            raise BasketNotFoundError(basket_id)
        except BasketNotFoundError as e:
            assert e.basket_id == basket_id
            assert "Basket" in str(e)

        try:
            message = "Invalid basket data"
            field = "quantity"
            raise BasketValidationError(message, field)
        except BasketValidationError as e:
            assert e.message == message
            assert e.field == field

        try:
            product_id = uuid4()
            raise InsufficientStockError(product_id, 10, 5)
        except InsufficientStockError as e:
            assert e.product_id == product_id
            assert e.requested_quantity == 10
            assert e.available_quantity == 5
            assert "Insufficient stock" in str(e)
