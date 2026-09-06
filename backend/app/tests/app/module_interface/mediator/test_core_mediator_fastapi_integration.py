"""Tests for FastAPI mediator integration."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.fastapi_integration import (
    configure_mediator, get_cancellation_token_dependency,
    get_handler_registry, get_handler_registry_dependency, get_mediator,
    get_mediator_dependency)
from app.core.mediator.handler_registry import HandlerRegistry
from app.core.mediator.mediator import Mediator
from fastapi import Request


class TestConfigureMediator:
    """Test configure_mediator function."""

    def test_configure_mediator_success(self) -> None:
        """Test successfully configuring mediator."""
        # Clear any existing configuration
        with patch("app.core.mediator.fastapi_integration._services", {}):
            configure_mediator()

            # Verify mediator was configured
            mediator = get_mediator()
            handler_registry = get_handler_registry()

            assert isinstance(mediator, Mediator)
            assert isinstance(handler_registry, HandlerRegistry)

    def test_configure_mediator_multiple_calls(self) -> None:
        """Test configuring mediator multiple times."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            # First configuration
            configure_mediator()
            mediator1 = get_mediator()
            registry1 = get_handler_registry()

            # Second configuration (should overwrite)
            configure_mediator()
            mediator2 = get_mediator()
            registry2 = get_handler_registry()

            # Should be different instances
            assert mediator1 is not mediator2
            assert registry1 is not registry2

    def test_configure_mediator_creates_new_instances(self) -> None:
        """Test that configure_mediator creates new instances."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            configure_mediator()

            mediator = get_mediator()
            handler_registry = get_handler_registry()

            # Verify they are properly connected
            assert mediator.handler_registry is handler_registry


class TestGetMediator:
    """Test get_mediator function."""

    def test_get_mediator_success(self) -> None:
        """Test successfully getting mediator."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            configure_mediator()
            mediator = get_mediator()

            assert isinstance(mediator, Mediator)

    def test_get_mediator_not_configured(self) -> None:
        """Test getting mediator when not configured."""
        with (
            patch("app.core.mediator.fastapi_integration._services", {}),
            pytest.raises(RuntimeError, match="Mediator not configured"),
        ):
            get_mediator()

    def test_get_mediator_none_value(self) -> None:
        """Test getting mediator when value is None."""
        with (
            patch(
                "app.core.mediator.fastapi_integration._services", {"mediator": None}
            ),
            pytest.raises(RuntimeError, match="Mediator not configured"),
        ):
            get_mediator()

    def test_get_mediator_empty_services(self) -> None:
        """Test getting mediator from empty services."""
        with (
            patch("app.core.mediator.fastapi_integration._services", {}),
            pytest.raises(RuntimeError, match="Mediator not configured"),
        ):
            get_mediator()


class TestGetHandlerRegistry:
    """Test get_handler_registry function."""

    def test_get_handler_registry_success(self) -> None:
        """Test successfully getting handler registry."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            configure_mediator()
            handler_registry = get_handler_registry()

            assert isinstance(handler_registry, HandlerRegistry)

    def test_get_handler_registry_not_configured(self) -> None:
        """Test getting handler registry when not configured."""
        with (
            patch("app.core.mediator.fastapi_integration._services", {}),
            pytest.raises(RuntimeError, match="Handler registry not configured"),
        ):
            get_handler_registry()

    def test_get_handler_registry_none_value(self) -> None:
        """Test getting handler registry when value is None."""
        with (
            patch(
                "app.core.mediator.fastapi_integration._services",
                {"handler_registry": None},
            ),
            pytest.raises(RuntimeError, match="Handler registry not configured"),
        ):
            get_handler_registry()

    def test_get_handler_registry_empty_services(self) -> None:
        """Test getting handler registry from empty services."""
        with (
            patch("app.core.mediator.fastapi_integration._services", {}),
            pytest.raises(RuntimeError, match="Handler registry not configured"),
        ):
            get_handler_registry()


class TestGetMediatorDependency:
    """Test get_mediator_dependency function."""

    def test_get_mediator_dependency_success(self) -> None:
        """Test successfully getting mediator dependency."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            configure_mediator()
            mediator = get_mediator_dependency()

            assert isinstance(mediator, Mediator)

    def test_get_mediator_dependency_not_configured(self) -> None:
        """Test getting mediator dependency when not configured."""
        with (
            patch("app.core.mediator.fastapi_integration._services", {}),
            pytest.raises(RuntimeError, match="Mediator not configured"),
        ):
            get_mediator_dependency()

    def test_get_mediator_dependency_returns_same_instance(self) -> None:
        """Test that dependency returns the same instance."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            configure_mediator()
            mediator1 = get_mediator_dependency()
            mediator2 = get_mediator_dependency()

            assert mediator1 is mediator2


class TestGetHandlerRegistryDependency:
    """Test get_handler_registry_dependency function."""

    def test_get_handler_registry_dependency_success(self) -> None:
        """Test successfully getting handler registry dependency."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            configure_mediator()
            handler_registry = get_handler_registry_dependency()

            assert isinstance(handler_registry, HandlerRegistry)

    def test_get_handler_registry_dependency_not_configured(self) -> None:
        """Test getting handler registry dependency when not configured."""
        with (
            patch("app.core.mediator.fastapi_integration._services", {}),
            pytest.raises(RuntimeError, match="Handler registry not configured"),
        ):
            get_handler_registry_dependency()

    def test_get_handler_registry_dependency_returns_same_instance(self) -> None:
        """Test that dependency returns the same instance."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            configure_mediator()
            registry1 = get_handler_registry_dependency()
            registry2 = get_handler_registry_dependency()

            assert registry1 is registry2


class TestGetCancellationTokenDependency:
    """Test get_cancellation_token_dependency function."""

    def test_get_cancellation_token_dependency_success(self) -> None:
        """Test successfully getting cancellation token dependency."""
        mock_request = MagicMock(spec=Request)

        with patch(
            "app.core.mediator.fastapi_integration.get_cancellation_token"
        ) as mock_get_token:
            mock_token = MagicMock(spec=CancellationToken)
            mock_get_token.return_value = mock_token

            result = get_cancellation_token_dependency(mock_request)

            assert result is mock_token
            mock_get_token.assert_called_once_with(mock_request)

    def test_get_cancellation_token_dependency_with_real_request(self) -> None:
        """Test getting cancellation token dependency with real request object."""
        mock_request = MagicMock(spec=Request)

        # Mock the get_cancellation_token function
        with patch(
            "app.core.mediator.fastapi_integration.get_cancellation_token"
        ) as mock_get_token:
            mock_token = MagicMock(spec=CancellationToken)
            mock_get_token.return_value = mock_token

            result = get_cancellation_token_dependency(mock_request)

            assert isinstance(result, MagicMock)
            mock_get_token.assert_called_once_with(mock_request)

    def test_get_cancellation_token_dependency_passes_request(self) -> None:
        """Test that the request is properly passed to get_cancellation_token."""
        mock_request = MagicMock(spec=Request)

        with patch(
            "app.core.mediator.fastapi_integration.get_cancellation_token"
        ) as mock_get_token:
            mock_get_token.return_value = MagicMock(spec=CancellationToken)

            get_cancellation_token_dependency(mock_request)

            # Verify the request was passed correctly
            mock_get_token.assert_called_once_with(mock_request)


class TestFastAPIIntegrationIntegration:
    """Integration tests for FastAPI mediator integration."""

    def test_full_integration_flow(self) -> None:
        """Test complete integration flow."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            # Configure mediator
            configure_mediator()

            # Get dependencies
            mediator = get_mediator_dependency()
            handler_registry = get_handler_registry_dependency()

            # Verify they work together
            assert isinstance(mediator, Mediator)
            assert isinstance(handler_registry, HandlerRegistry)
            assert mediator.handler_registry is handler_registry

    def test_dependency_injection_flow(self) -> None:
        """Test dependency injection flow."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            # Configure mediator
            configure_mediator()

            # Simulate FastAPI dependency injection
            mediator_dep = get_mediator_dependency()
            registry_dep = get_handler_registry_dependency()

            # Verify dependencies are properly configured
            assert mediator_dep is not None
            assert registry_dep is not None
            assert mediator_dep.handler_registry is registry_dep

    def test_cancellation_token_integration(self) -> None:
        """Test cancellation token integration."""
        mock_request = MagicMock(spec=Request)

        with patch(
            "app.core.mediator.fastapi_integration.get_cancellation_token"
        ) as mock_get_token:
            mock_token = MagicMock(spec=CancellationToken)
            mock_get_token.return_value = mock_token

            # Get cancellation token dependency
            token = get_cancellation_token_dependency(mock_request)

            # Verify integration
            assert token is mock_token
            mock_get_token.assert_called_once_with(mock_request)

    def test_error_handling_integration(self) -> None:
        """Test error handling in integration."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            # Try to get mediator without configuration
            with pytest.raises(RuntimeError, match="Mediator not configured"):
                get_mediator_dependency()

            with pytest.raises(RuntimeError, match="Handler registry not configured"):
                get_handler_registry_dependency()

    def test_multiple_configurations(self) -> None:
        """Test multiple configurations and their effects."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            # First configuration
            configure_mediator()
            mediator1 = get_mediator_dependency()
            registry1 = get_handler_registry_dependency()

            # Second configuration
            configure_mediator()
            mediator2 = get_mediator_dependency()
            registry2 = get_handler_registry_dependency()

            # Should be different instances
            assert mediator1 is not mediator2
            assert registry1 is not registry2

    def test_services_isolation(self) -> None:
        """Test that services are properly isolated."""
        # Test with different service containers
        services1: dict[Any, Any] = {}
        services2: dict[Any, Any] = {}

        with patch("app.core.mediator.fastapi_integration._services", services1):
            configure_mediator()
            mediator1 = get_mediator_dependency()

        with patch("app.core.mediator.fastapi_integration._services", services2):
            configure_mediator()
            mediator2 = get_mediator_dependency()

        # Should be different instances
        assert mediator1 is not mediator2

    def test_fastapi_request_integration(self) -> None:
        """Test integration with FastAPI Request object."""
        # Create a more realistic mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.method = "GET"
        mock_request.url = "http://localhost:8000/test"

        with patch(
            "app.core.mediator.fastapi_integration.get_cancellation_token"
        ) as mock_get_token:
            mock_token = MagicMock(spec=CancellationToken)
            mock_get_token.return_value = mock_token

            token = get_cancellation_token_dependency(mock_request)

            assert token is mock_token
            mock_get_token.assert_called_once_with(mock_request)

    def test_mediator_functionality_after_integration(self) -> None:
        """Test that mediator works correctly after integration."""
        with patch("app.core.mediator.fastapi_integration._services", {}):
            configure_mediator()
            mediator = get_mediator_dependency()

            # Test that mediator can register and handle requests
            from app.core.contracts.cqrs import ICommand as Command
            from app.core.cqrs.base import CommandResult as Result

            class TestCommand(Command[Result]):
                pass

            class TestResult(Result):
                success: bool = True

            class TestHandler:
                async def handle(
                    self,
                    request: TestCommand,  # noqa: ARG002
                ) -> TestResult:
                    return TestResult()

            # Register handler
            mediator.register_handler(TestCommand, TestHandler())

            # Verify handler was registered
            assert TestCommand in mediator.handler_registry.get_registered_types()
