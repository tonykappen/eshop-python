"""Tests for authorization behavior."""

import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import directly from file to avoid circular import issues
# Use absolute path to avoid path calculation issues
# Test file is at: backend/app/tests/app/core/application/behaviors/test_authorization_behavior.py
# Target file is at: backend/app/core/application/behaviors/authorization_behavior.py
# Need to go up 7 levels to get to backend/, then add app/core/...
auth_behavior_path = (
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent
    / "app"
    / "core"
    / "application"
    / "behaviors"
    / "authorization_behavior.py"
)

spec = importlib.util.spec_from_file_location(
    "authorization_behavior",
    auth_behavior_path,
)
authorization_behavior_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authorization_behavior_module)  # type: ignore[union-attr]
AuthorizationBehavior = authorization_behavior_module.AuthorizationBehavior


class TestAuthorizationBehavior:
    """Test AuthorizationBehavior."""

    @pytest.fixture
    def authorization_behavior(self) -> AuthorizationBehavior:
        """Provide AuthorizationBehavior instance."""
        return AuthorizationBehavior()

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """Provide mock logger."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_handle_allows_request(
        self, authorization_behavior: AuthorizationBehavior
    ) -> None:
        """Test that handle allows requests through."""
        # Create a mock request
        mock_request = MagicMock()
        mock_request.__class__.__name__ = "TestCommand"

        # Create a mock next handler
        mock_response = MagicMock()
        next_handler = AsyncMock(return_value=mock_response)

        # Execute
        result = await authorization_behavior.handle(mock_request, next_handler)

        # Assert
        assert result == mock_response
        next_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_logs_authorization_check(
        self,
        authorization_behavior: AuthorizationBehavior,
        mock_logger: MagicMock,
    ) -> None:
        """Test that handle logs authorization check."""
        with patch.object(authorization_behavior, "logger", mock_logger):
            mock_request = MagicMock()
            mock_request.__class__.__name__ = "TestCommand"

            next_handler = AsyncMock(return_value=MagicMock())

            await authorization_behavior.handle(mock_request, next_handler)

            # Verify log was called
            mock_logger.log_debug_with_context.assert_called_once()
            call_args = mock_logger.log_debug_with_context.call_args
            assert "Authorization check" in call_args[0][0]
            assert call_args[1]["context"]["request_type"] == "TestCommand"

    @pytest.mark.asyncio
    async def test_handle_with_different_request_types(
        self, authorization_behavior: AuthorizationBehavior
    ) -> None:
        """Test handle with different request types."""
        request_types = [
            "CreateProductCommand",
            "GetProductQuery",
            "UpdateOrderCommand",
        ]

        for request_type in request_types:
            mock_request = MagicMock()
            mock_request.__class__.__name__ = request_type

            next_handler = AsyncMock(return_value=MagicMock())

            result = await authorization_behavior.handle(mock_request, next_handler)

            assert result is not None
            next_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_propagates_exceptions(
        self, authorization_behavior: AuthorizationBehavior
    ) -> None:
        """Test that handle propagates exceptions from next handler."""
        mock_request = MagicMock()
        mock_request.__class__.__name__ = "TestCommand"

        test_exception = ValueError("Test error")
        next_handler = AsyncMock(side_effect=test_exception)

        with pytest.raises(ValueError, match="Test error"):
            await authorization_behavior.handle(mock_request, next_handler)

        next_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_with_response(
        self, authorization_behavior: AuthorizationBehavior
    ) -> None:
        """Test handle with a response value."""
        mock_request = MagicMock()
        mock_request.__class__.__name__ = "TestCommand"

        expected_response = {"id": 123, "name": "Test"}
        next_handler = AsyncMock(return_value=expected_response)

        result = await authorization_behavior.handle(mock_request, next_handler)

        assert result == expected_response
        next_handler.assert_called_once()
