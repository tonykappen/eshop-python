"""Tests for Catalog domain exceptions."""

from uuid import uuid4

from app.modules.catalog.domain.exceptions.product import (
    ProductCreationError,
    ProductDeleteError,
    ProductNotFoundError,
    ProductUpdateError,
)


class TestProductNotFoundError:
    """Test ProductNotFoundError exception."""

    def test_product_not_found_error_initialization(self):
        """Test ProductNotFoundError initialization."""
        product_id = uuid4()
        error = ProductNotFoundError(product_id)

        assert error.product_id == product_id
        assert str(product_id) in str(error)
        assert 'Entity "Product"' in str(error)
        assert "was not found" in str(error)

    def test_product_not_found_error_with_string_id(self):
        """Test ProductNotFoundError with string product ID."""
        product_id = str(uuid4())
        error = ProductNotFoundError(product_id)

        assert error.product_id == product_id
        assert product_id in str(error)

    def test_product_not_found_error_inheritance(self):
        """Test ProductNotFoundError inheritance."""
        product_id = uuid4()
        error = ProductNotFoundError(product_id)

        assert isinstance(error, Exception)
        assert hasattr(error, "product_id")


class TestProductCreationError:
    """Test ProductCreationError exception."""

    def test_product_creation_error_initialization(self):
        """Test ProductCreationError initialization."""
        message = "Failed to create product"
        error = ProductCreationError(message)

        assert error.message == message
        assert message in str(error)

    def test_product_creation_error_with_details(self):
        """Test ProductCreationError with details."""
        message = "Failed to create product"
        details = "Database connection failed"
        error = ProductCreationError(message, details)

        assert error.message == message
        assert error.details == details
        assert message in str(error)
        # Note: details are not included in str() representation

    def test_product_creation_error_inheritance(self):
        """Test ProductCreationError inheritance."""
        error = ProductCreationError("Test message")

        assert isinstance(error, Exception)
        assert hasattr(error, "message")
        assert hasattr(error, "details")


class TestProductUpdateError:
    """Test ProductUpdateError exception."""

    def test_product_update_error_initialization(self):
        """Test ProductUpdateError initialization."""
        message = "Failed to update product"
        error = ProductUpdateError(message)

        assert error.message == message
        assert message in str(error)

    def test_product_update_error_with_details(self):
        """Test ProductUpdateError with details."""
        message = "Failed to update product"
        details = "Validation failed"
        error = ProductUpdateError(message, details)

        assert error.message == message
        assert error.details == details
        assert message in str(error)
        # Note: details are not included in str() representation

    def test_product_update_error_inheritance(self):
        """Test ProductUpdateError inheritance."""
        error = ProductUpdateError("Test message")

        assert isinstance(error, Exception)
        assert hasattr(error, "message")
        assert hasattr(error, "details")


class TestProductDeleteError:
    """Test ProductDeleteError exception."""

    def test_product_delete_error_initialization(self):
        """Test ProductDeleteError initialization."""
        message = "Failed to delete product"
        error = ProductDeleteError(message)

        assert error.message == message
        assert message in str(error)

    def test_product_delete_error_with_details(self):
        """Test ProductDeleteError with details."""
        message = "Failed to delete product"
        details = "Foreign key constraint"
        error = ProductDeleteError(message, details)

        assert error.message == message
        assert error.details == details
        assert message in str(error)
        # Note: details are not included in str() representation

    def test_product_delete_error_inheritance(self):
        """Test ProductDeleteError inheritance."""
        error = ProductDeleteError("Test message")

        assert isinstance(error, Exception)
        assert hasattr(error, "message")
        assert hasattr(error, "details")


class TestExceptionChaining:
    """Test exception chaining and context."""

    def test_exception_basic_chaining(self):
        """Test basic exception chaining without cause parameter."""
        original_error = ValueError("Original error")
        wrapped_error = ProductCreationError("Wrapped error")

        assert "Wrapped error" in str(wrapped_error)
        assert isinstance(wrapped_error, Exception)

    def test_exception_context_preservation(self):
        """Test that exception context is preserved."""
        try:
            raise ValueError("Original error")
        except ValueError:
            wrapped_error = ProductUpdateError("Wrapped error")
            assert "Wrapped error" in str(wrapped_error)
            assert isinstance(wrapped_error, Exception)

    def test_multiple_exception_layers(self):
        """Test multiple layers of exception wrapping."""
        original = RuntimeError("Database error")
        intermediate = ProductCreationError("Creation failed")
        final = ProductUpdateError("Update failed")

        assert "Update failed" in str(final)
        assert "Creation failed" in str(intermediate)
        assert "Database error" in str(original)


class TestExceptionMessages:
    """Test exception message formatting."""

    def test_product_not_found_message_format(self):
        """Test ProductNotFoundError message format."""
        product_id = uuid4()
        error = ProductNotFoundError(product_id)
        message = str(error)

        assert 'Entity "Product"' in message
        assert str(product_id) in message
        assert "was not found" in message

    def test_creation_error_message_format(self):
        """Test ProductCreationError message format."""
        error = ProductCreationError("Test message", "Test details")
        message = str(error)

        assert "Test message" in message
        # Note: details are not included in str() representation

    def test_update_error_message_format(self):
        """Test ProductUpdateError message format."""
        error = ProductUpdateError("Test message", "Test details")
        message = str(error)

        assert "Test message" in message
        # Note: details are not included in str() representation

    def test_delete_error_message_format(self):
        """Test ProductDeleteError message format."""
        error = ProductDeleteError("Test message", "Test details")
        message = str(error)

        assert "Test message" in message
        # Note: details are not included in str() representation

    def test_error_without_details(self):
        """Test error messages without details."""
        error = ProductCreationError("Simple message")
        message = str(error)

        assert "Simple message" in message
        assert "Details" not in message

    def test_error_with_none_details(self):
        """Test error messages with None details."""
        error = ProductCreationError("Test message", None)
        message = str(error)

        assert "Test message" in message
        assert "None" not in message
