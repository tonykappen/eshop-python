"""Tests for custom exception handling system."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from eshop.core.exceptions.base import (
    BadRequestError,
    BaseError,
    ConfigurationError,
    ConflictError,
    ConnectionError,
    DatabaseError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    UnauthorizedError,
)
from eshop.core.exceptions.base import (
    ValidationError as CustomValidationError,
)
from eshop.core.exceptions.handler import CustomExceptionHandler
from eshop.modules.catalog.domain.exceptions import ProductNotFoundError


class TestBaseExceptions:
    """Test base exception classes."""

    def test_base_error_initialization(self):
        """Test BaseError initialization."""
        error = BaseError("Test error", "Test details")
        assert error.message == "Test error"
        assert error.details == "Test details"
        assert str(error) == "Test error"

    def test_bad_request_error(self):
        """Test BadRequestError."""
        error = BadRequestError("Bad request", "Invalid data")
        assert error.message == "Bad request"
        assert error.details == "Invalid data"

    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("Resource not found")
        assert error.message == "Resource not found"

    def test_not_found_error_with_name_and_key(self):
        """Test NotFoundError with name and key."""
        error = NotFoundError(name="Product", key="123")
        assert error.message == 'Entity "Product" (123) was not found.'

    def test_internal_server_error(self):
        """Test InternalServerError."""
        error = InternalServerError("Server error", "Database connection failed")
        assert error.message == "Server error"
        assert error.details == "Database connection failed"

    def test_validation_error(self):
        """Test ValidationError."""
        errors = {"field": "error message"}
        error = CustomValidationError("Validation failed", errors, "Invalid input")
        assert error.message == "Validation failed"
        assert error.errors == errors
        assert error.details == "Invalid input"

    def test_unauthorized_error(self):
        """Test UnauthorizedError."""
        error = UnauthorizedError("Access denied", "Invalid token")
        assert error.message == "Access denied"
        assert error.details == "Invalid token"

    def test_forbidden_error(self):
        """Test ForbiddenError."""
        error = ForbiddenError("Access forbidden", "Insufficient permissions")
        assert error.message == "Access forbidden"
        assert error.details == "Insufficient permissions"

    def test_conflict_error(self):
        """Test ConflictError."""
        error = ConflictError("Resource conflict", "Duplicate entry")
        assert error.message == "Resource conflict"
        assert error.details == "Duplicate entry"

    def test_database_error(self):
        """Test DatabaseError."""
        error = DatabaseError("Database error", "Connection timeout")
        assert error.message == "Database error"
        assert error.details == "Connection timeout"

    def test_connection_error(self):
        """Test ConnectionError."""
        error = ConnectionError("Connection failed", "Network timeout")
        assert error.message == "Connection failed"
        assert error.details == "Network timeout"

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Config error", "Missing required setting")
        assert error.message == "Config error"
        assert error.details == "Missing required setting"


class TestCustomExceptionHandler:
    """Test custom exception handler."""

    def test_map_internal_server_error(self):
        """Test mapping InternalServerError."""
        error = InternalServerError("Server error", "Database failed")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 500
        assert title == "InternalServerError"
        assert detail == "Server error"
        assert extensions["details"] == "Database failed"

    def test_map_bad_request_error(self):
        """Test mapping BadRequestError."""
        error = BadRequestError("Bad request", "Invalid data")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 400
        assert title == "BadRequestError"
        assert detail == "Bad request"
        assert extensions["details"] == "Invalid data"

    def test_map_not_found_error(self):
        """Test mapping NotFoundError."""
        error = NotFoundError("Not found")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 404
        assert title == "NotFoundError"
        assert detail == "Not found"

    def test_map_validation_error(self):
        """Test mapping ValidationError."""
        errors = {"field": "error"}
        error = CustomValidationError("Validation failed", errors)
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 400
        assert title == "ValidationError"
        assert detail == "Validation failed"
        assert extensions["validationErrors"] == errors

    def test_map_unauthorized_error(self):
        """Test mapping UnauthorizedError."""
        error = UnauthorizedError("Unauthorized")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 401
        assert title == "UnauthorizedError"
        assert detail == "Unauthorized"

    def test_map_forbidden_error(self):
        """Test mapping ForbiddenError."""
        error = ForbiddenError("Forbidden")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 403
        assert title == "ForbiddenError"
        assert detail == "Forbidden"

    def test_map_conflict_error(self):
        """Test mapping ConflictError."""
        error = ConflictError("Conflict")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 409
        assert title == "ConflictError"
        assert detail == "Conflict"

    def test_map_database_error(self):
        """Test mapping DatabaseError."""
        error = DatabaseError("Database error")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 500
        assert title == "DatabaseError"
        assert detail == "Database error"

    def test_map_connection_error(self):
        """Test mapping ConnectionError."""
        error = ConnectionError("Connection failed")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 503
        assert title == "ConnectionError"
        assert detail == "Connection failed"

    def test_map_configuration_error(self):
        """Test mapping ConfigurationError."""
        error = ConfigurationError("Config error")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 500
        assert title == "ConfigurationError"
        assert detail == "Config error"

    def test_map_pydantic_validation_error(self):
        """Test mapping Pydantic ValidationError."""
        class TestModel(BaseModel):
            name: str
            age: int

        try:
            TestModel(name="", age="invalid")
        except ValidationError as e:
            status_code, title, detail, extensions = CustomExceptionHandler._map_exception(e)

            assert status_code == 400
            assert title == "ValidationError"
            assert detail == "Request validation failed"

    def test_map_generic_exception(self):
        """Test mapping generic exception."""
        error = Exception("Generic error")
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(error)

        assert status_code == 500
        assert title == "Exception"
        assert detail == "Generic error"
        assert "traceback" in extensions


class TestDomainExceptions:
    """Test domain-specific exceptions."""

    def test_product_not_found_error(self):
        """Test ProductNotFoundError."""
        from uuid import uuid4
        product_id = uuid4()
        error = ProductNotFoundError(product_id)

        assert error.product_id == product_id
        assert error.message == f'Entity "Product" ({product_id}) was not found.'


class TestExceptionHandlerIntegration:
    """Test exception handler integration with FastAPI."""

    def test_exception_handler_integration(self):
        """Test exception handler integration."""
        app = FastAPI()

        @app.get("/test-bad-request")
        def test_bad_request():
            raise BadRequestError("Bad request", "Invalid data")

        @app.get("/test-not-found")
        def test_not_found():
            raise NotFoundError("Resource not found")

        @app.get("/test-internal-server")
        def test_internal_server():
            raise InternalServerError("Server error", "Database failed")

        # Add exception handlers
        from eshop.core.exceptions.handler import add_exception_handlers
        add_exception_handlers(app)

        client = TestClient(app)

        # Test bad request
        response = client.get("/test-bad-request")
        assert response.status_code == 400
        data = response.json()
        assert data["title"] == "BadRequestError"
        assert data["detail"] == "Bad request"
        assert data["details"] == "Invalid data"

        # Test not found
        response = client.get("/test-not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["title"] == "NotFoundError"
        assert data["detail"] == "Resource not found"

        # Test internal server error
        response = client.get("/test-internal-server")
        assert response.status_code == 500
        data = response.json()
        assert data["title"] == "InternalServerError"
        assert data["detail"] == "Server error"
        assert data["details"] == "Database failed"
