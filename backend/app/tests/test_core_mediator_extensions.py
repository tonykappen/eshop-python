"""Tests for mediator extensions."""

from unittest.mock import MagicMock, patch

from app.core.contracts.cqrs import ICommand as Command
from app.core.contracts.cqrs import IQuery as Query
from app.core.cqrs.base import CommandResult as Result
from app.core.mediator.extensions import (
    _extract_request_type,
    _is_request_handler,
    _register_handlers_from_assembly,
    add_mediator_with_assemblies,
    get_handler_registry,
    get_mediator,
)
from app.core.mediator.handler_registry import HandlerRegistry
from app.core.mediator.mediator import Mediator


class MockCommand(Command[Result]):
    """Mock command for testing."""

    pass


class MockQuery(Query[Result]):
    """Mock query for testing."""

    pass


class MockResult(Result):
    """Mock result for testing."""

    pass


class MockRequestHandler:
    """Mock request handler for testing."""

    async def handle(self, request: MockCommand) -> MockResult:  # noqa: ARG002
        """Handle the request."""
        return MockResult()


class MockQueryHandler:
    """Mock query handler for testing."""

    async def handle(self, request: MockQuery) -> MockResult:  # noqa: ARG002
        """Handle the query."""
        return MockResult()


class MockIRequestHandler:
    """Mock IRequestHandler interface."""

    pass


class MockHandlerWithIRequestHandler(MockIRequestHandler):
    """Mock handler implementing IRequestHandler."""

    async def handle(self, request: MockCommand) -> MockResult:  # noqa: ARG002
        """Handle the request."""
        return MockResult()


class MockAbstractHandler:
    """Mock abstract handler for testing."""

    async def handle(self, request: MockCommand) -> MockResult:  # noqa: ARG002
        """Handle the request."""
        return MockResult()


class MockHandlerWithoutHandle:
    """Mock handler without handle method."""

    pass


class MockHandlerWithNonAsyncHandle:
    """Mock handler with non-async handle method."""

    def handle(self, request: MockCommand) -> MockResult:  # noqa: ARG002
        """Handle the request."""
        return MockResult()


class MockHandlerWithGenericBase:
    """Mock handler with generic base class."""

    async def handle(self, request: MockCommand) -> MockResult:  # noqa: ARG002
        """Handle the request."""
        return MockResult()


class MockHandlerWithMethodSignature:
    """Mock handler with method signature."""

    async def handle(self, request: MockCommand) -> MockResult:  # noqa: ARG002
        """Handle the request."""
        return MockResult()


class TestAddMediatorWithAssemblies:
    """Test add_mediator_with_assemblies function."""

    def test_add_mediator_with_assemblies_success(self) -> None:
        """Test successfully adding mediator with assemblies."""
        services = {}

        # Create mock assembly with handlers
        mock_assembly = MagicMock()
        mock_assembly.__name__ = "test_assembly"

        # Mock getmembers to return our test handlers
        with patch(
            "app.core.mediator.extensions.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = [
                ("MockRequestHandler", MockRequestHandler),
                ("MockQueryHandler", MockQueryHandler),
            ]

            result = add_mediator_with_assemblies(services, mock_assembly)

        assert result is services
        assert "mediator" in services
        assert "handler_registry" in services
        assert isinstance(services["mediator"], Mediator)
        assert isinstance(services["handler_registry"], HandlerRegistry)

    def test_add_mediator_with_multiple_assemblies(self) -> None:
        """Test adding mediator with multiple assemblies."""
        services = {}

        mock_assembly1 = MagicMock()
        mock_assembly1.__name__ = "test_assembly1"
        mock_assembly2 = MagicMock()
        mock_assembly2.__name__ = "test_assembly2"

        with patch(
            "app.core.mediator.extensions.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = [
                ("MockRequestHandler", MockRequestHandler),
            ]

            result = add_mediator_with_assemblies(
                services, mock_assembly1, mock_assembly2
            )

        assert result is services
        assert "mediator" in services
        assert "handler_registry" in services

    def test_add_mediator_with_no_handlers(self) -> None:
        """Test adding mediator with no handlers found."""
        services = {}

        mock_assembly = MagicMock()
        mock_assembly.__name__ = "test_assembly"

        with patch(
            "app.core.mediator.extensions.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = []

            result = add_mediator_with_assemblies(services, mock_assembly)

        assert result is services
        assert "mediator" in services
        assert "handler_registry" in services
        # Should still create mediator and registry even with no handlers
        assert isinstance(services["mediator"], Mediator)
        assert isinstance(services["handler_registry"], HandlerRegistry)


class TestRegisterHandlersFromAssembly:
    """Test _register_handlers_from_assembly function."""

    def test_register_handlers_from_assembly_success(self) -> None:
        """Test successfully registering handlers from assembly."""
        handler_registry = HandlerRegistry()
        mock_assembly = MagicMock()

        with patch(
            "app.core.mediator.extensions.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = [
                ("MockRequestHandler", MockRequestHandler),
                ("MockQueryHandler", MockQueryHandler),
            ]

            _register_handlers_from_assembly(handler_registry, mock_assembly)

        # Check that handlers were registered
        registered_types = handler_registry.get_registered_types()
        assert len(registered_types) == 2
        assert MockCommand in registered_types
        assert MockQuery in registered_types

    def test_register_handlers_from_assembly_no_handlers(self) -> None:
        """Test registering handlers from assembly with no valid handlers."""
        handler_registry = HandlerRegistry()
        mock_assembly = MagicMock()

        with patch(
            "app.core.mediator.extensions.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = [
                ("MockHandlerWithoutHandle", MockHandlerWithoutHandle),
                ("MockHandlerWithNonAsyncHandle", MockHandlerWithNonAsyncHandle),
            ]

            _register_handlers_from_assembly(handler_registry, mock_assembly)

        # Check that no handlers were registered
        registered_types = handler_registry.get_registered_types()
        assert len(registered_types) == 0

    def test_register_handlers_from_assembly_mixed_handlers(self) -> None:
        """Test registering handlers from assembly with mixed valid and invalid handlers."""
        handler_registry = HandlerRegistry()
        mock_assembly = MagicMock()

        with patch(
            "app.core.mediator.extensions.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = [
                ("MockRequestHandler", MockRequestHandler),
                ("MockHandlerWithoutHandle", MockHandlerWithoutHandle),
                ("MockQueryHandler", MockQueryHandler),
            ]

            _register_handlers_from_assembly(handler_registry, mock_assembly)

        # Check that only valid handlers were registered
        registered_types = handler_registry.get_registered_types()
        assert len(registered_types) == 2
        assert MockCommand in registered_types
        assert MockQuery in registered_types


class TestIsRequestHandler:
    """Test _is_request_handler function."""

    def test_is_request_handler_with_handle_method(self) -> None:
        """Test handler with async handle method."""
        assert _is_request_handler(MockRequestHandler) is True

    def test_is_request_handler_with_query_handler(self) -> None:
        """Test query handler with async handle method."""
        assert _is_request_handler(MockQueryHandler) is True

    def test_is_request_handler_with_i_request_handler(self) -> None:
        """Test handler implementing IRequestHandler."""
        assert _is_request_handler(MockHandlerWithIRequestHandler) is True

    def test_is_request_handler_abstract_class(self) -> None:
        """Test abstract handler class."""
        # Make the class abstract
        MockAbstractHandler.__abstractmethods__ = frozenset(["abstract_method"])
        assert _is_request_handler(MockAbstractHandler) is False

    def test_is_request_handler_without_handle_method(self) -> None:
        """Test class without handle method."""
        assert _is_request_handler(MockHandlerWithoutHandle) is False

    def test_is_request_handler_with_non_async_handle(self) -> None:
        """Test handler with non-async handle method."""
        assert _is_request_handler(MockHandlerWithNonAsyncHandle) is False

    def test_is_request_handler_regular_class(self) -> None:
        """Test regular class that's not a handler."""

        class RegularClass:
            pass

        assert _is_request_handler(RegularClass) is False


class TestExtractRequestType:
    """Test _extract_request_type function."""

    def test_extract_request_type_from_generic_base(self) -> None:
        """Test extracting request type from generic base."""

        # Create a handler with generic base
        class GenericHandler:
            __orig_bases__ = ((MockCommand, MockResult),)
            __args__ = (MockCommand, MockResult)

        request_type = _extract_request_type(GenericHandler)
        assert request_type == MockCommand

    def test_extract_request_type_from_method_signature(self) -> None:
        """Test extracting request type from method signature."""
        request_type = _extract_request_type(MockRequestHandler)
        assert request_type == MockCommand

    def test_extract_request_type_from_query_handler(self) -> None:
        """Test extracting request type from query handler."""
        request_type = _extract_request_type(MockQueryHandler)
        assert request_type == MockQuery

    def test_extract_request_type_no_generic_base(self) -> None:
        """Test extracting request type when no generic base exists."""

        class HandlerWithoutGenericBase:
            async def handle(self, _request: MockCommand) -> MockResult:
                return MockResult()

        request_type = _extract_request_type(HandlerWithoutGenericBase)
        assert request_type == MockCommand

    def test_extract_request_type_no_method_signature(self) -> None:
        """Test extracting request type when no method signature exists."""

        class HandlerWithoutMethodSignature:
            pass

        request_type = _extract_request_type(HandlerWithoutMethodSignature)
        assert request_type is None

    def test_extract_request_type_empty_generic_args(self) -> None:
        """Test extracting request type with empty generic args."""

        class HandlerWithEmptyGenericArgs:
            __orig_bases__ = ((),)

        request_type = _extract_request_type(HandlerWithEmptyGenericArgs)
        assert request_type is None

    def test_extract_request_type_no_orig_bases(self) -> None:
        """Test extracting request type when __orig_bases__ doesn't exist."""

        class HandlerWithoutOrigBases:
            async def handle(self, request: MockCommand) -> MockResult:  # noqa: ARG002
                return MockResult()

        request_type = _extract_request_type(HandlerWithoutOrigBases)
        assert request_type == MockCommand

    def test_extract_request_type_method_without_annotation(self) -> None:
        """Test extracting request type from method without annotation."""

        class HandlerWithoutAnnotation:
            async def handle(self, _request) -> MockResult:  # type: ignore[no-untyped-def]
                return MockResult()

        request_type = _extract_request_type(HandlerWithoutAnnotation)
        assert request_type is None

    def test_extract_request_type_method_with_wrong_param_name(self) -> None:
        """Test extracting request type from method with wrong parameter name."""

        class HandlerWithWrongParamName:
            async def handle(self, cmd: MockCommand) -> MockResult:  # noqa: ARG002
                return MockResult()

        request_type = _extract_request_type(HandlerWithWrongParamName)
        assert request_type is None


class TestGetMediator:
    """Test get_mediator function."""

    def test_get_mediator_success(self) -> None:
        """Test successfully getting mediator from services."""
        mediator = Mediator(HandlerRegistry())
        services = {"mediator": mediator}

        result = get_mediator(services)
        assert result is mediator

    def test_get_mediator_not_found(self) -> None:
        """Test getting mediator when not found in services."""
        services = {}

        result = get_mediator(services)
        assert result is None

    def test_get_mediator_empty_services(self) -> None:
        """Test getting mediator from empty services."""
        result = get_mediator({})
        assert result is None


class TestGetHandlerRegistry:
    """Test get_handler_registry function."""

    def test_get_handler_registry_success(self) -> None:
        """Test successfully getting handler registry from services."""
        handler_registry = HandlerRegistry()
        services = {"handler_registry": handler_registry}

        result = get_handler_registry(services)
        assert result is handler_registry

    def test_get_handler_registry_not_found(self) -> None:
        """Test getting handler registry when not found in services."""
        services = {}

        result = get_handler_registry(services)
        assert result is None

    def test_get_handler_registry_empty_services(self) -> None:
        """Test getting handler registry from empty services."""
        result = get_handler_registry({})
        assert result is None


class TestMediatorExtensionsIntegration:
    """Integration tests for mediator extensions."""

    def test_full_mediator_registration_flow(self) -> None:
        """Test complete mediator registration flow."""
        services = {}

        # Create mock assembly
        mock_assembly = MagicMock()
        mock_assembly.__name__ = "test_assembly"

        # Mock getmembers to return our test handlers
        with patch(
            "app.core.mediator.extensions.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = [
                ("MockRequestHandler", MockRequestHandler),
                ("MockQueryHandler", MockQueryHandler),
            ]

            # Add mediator with assemblies
            result = add_mediator_with_assemblies(services, mock_assembly)

            # Get mediator and handler registry
            mediator = get_mediator(services)
            handler_registry = get_handler_registry(services)

        # Verify the flow worked correctly
        assert result is services
        assert mediator is not None
        assert handler_registry is not None
        assert isinstance(mediator, Mediator)
        assert isinstance(handler_registry, HandlerRegistry)

        # Verify handlers were registered
        registered_types = handler_registry.get_registered_types()
        assert len(registered_types) == 2
        assert MockCommand in registered_types
        assert MockQuery in registered_types

    def test_mediator_extensions_with_real_handlers(self) -> None:
        """Test mediator extensions with real handler instances."""
        services = {}

        # Create a real assembly-like object
        class TestAssembly:
            class RealCommandHandler:
                async def handle(self, _request: MockCommand) -> MockResult:
                    return MockResult()

            class RealQueryHandler:
                async def handle(self, _request: MockQuery) -> MockResult:
                    return MockResult()

        # Add mediator with the test assembly
        result = add_mediator_with_assemblies(services, TestAssembly)

        # Verify registration
        mediator = get_mediator(services)
        handler_registry = get_handler_registry(services)

        assert result is services
        assert mediator is not None
        assert handler_registry is not None

        # Verify handlers were registered
        registered_types = handler_registry.get_registered_types()
        assert len(registered_types) == 2
        assert MockCommand in registered_types
        assert MockQuery in registered_types

    def test_mediator_extensions_error_handling(self) -> None:
        """Test error handling in mediator extensions."""
        services = {}

        # Create mock assembly that will cause errors
        mock_assembly = MagicMock()
        mock_assembly.__name__ = "test_assembly"

        # Mock getmembers to raise an exception
        with patch(
            "app.core.mediator.extensions.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.side_effect = Exception("Assembly scan failed")

            # Should not raise exception, should handle gracefully
            result = add_mediator_with_assemblies(services, mock_assembly)

        # Should still create mediator and registry
        assert result is services
        assert "mediator" in services
        assert "handler_registry" in services
        assert isinstance(services["mediator"], Mediator)
        assert isinstance(services["handler_registry"], HandlerRegistry)
