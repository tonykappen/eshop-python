"""Tests for common exception classes."""

from uuid import uuid4

import pytest
from app.core.exceptions.common_exceptions import (
    BaseError,
    ConflictError,
    ConfigurationError,
    ConnectionError,
    DatabaseError,
    DomainException,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestCommonExceptions:
    def test_base_error(self) -> None:
        err = BaseError("failed", details="more")
        assert str(err) == "failed"
        assert err.details == "more"

    def test_validation_error(self) -> None:
        err = ValidationError(errors={"name": "required"})
        assert err.errors["name"] == "required"

    def test_not_found_with_entity(self) -> None:
        key = uuid4()
        err = NotFoundError(name="Product", key=key)
        assert "Product" in err.message
        assert str(key) in err.message

    def test_standard_http_errors(self) -> None:
        assert UnauthorizedError().message == "Unauthorized access"
        assert ForbiddenError().message == "Access forbidden"
        assert ConflictError().message == "Resource conflict"

    def test_infrastructure_errors(self) -> None:
        assert DatabaseError().message == "Database error"
        assert ConnectionError().message == "Connection error"
        assert ConfigurationError().message == "Configuration error"
        assert DomainException().message == "Domain error"
