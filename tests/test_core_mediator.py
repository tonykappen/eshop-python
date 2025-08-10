"""Comprehensive tests for the core mediator pattern implementation."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request

from eshop.core.contracts.cqrs import ICommand, IQuery
from eshop.core.mediator.behaviors import (
    BehaviorWrapper,
    IPipelineBehavior,
    LoggingBehavior,
    ValidationBehavior,
)
from eshop.core.mediator.cancellation import (
    CancellationError,
    CancellationToken,
    create_cancellation_token,
    get_cancellation_token,
    get_global_cancellation_token,
)
from eshop.core.mediator.handler_registry import HandlerRegistry, IRequestHandler
from eshop.core.mediator.mediator import Mediator


@pytest.mark.no_collect
class TestCommand(ICommand[str]):
    """Test command for testing."""

    name: str


@pytest.mark.no_collect
class TestQuery(IQuery[str]):
    """Test query for testing."""

    id: str


class TestCommandHandler(IRequestHandler[TestCommand, str]):
    """Test command handler."""

    async def handle(
        self,
        request: TestCommand,
        cancellation_token: CancellationToken,  # noqa: ARG002
    ) -> str:
        return f"Command executed: {request.name}"


class TestQueryHandler(IRequestHandler[TestQuery, str]):
    """Test query handler."""

    async def handle(
        self, request: TestQuery, cancellation_token: CancellationToken  # noqa: ARG002
    ) -> str:
        return f"Query result: {request.id}"


@pytest.mark.no_collect
class TestBehavior(IPipelineBehavior[TestCommand, str]):
    """Test pipeline behavior."""

    def __init__(self, name: str):
        self.name = name
        self.called = False

    async def handle(self, request: TestCommand, next_handler) -> str:  # noqa: ARG002
        self.called = True
        result = await next_handler()
        return f"{self.name}: {result}"


class TestCancellationToken:
    """Test CancellationToken class."""

    def test_cancellation_token_initialization(self):
        """Test CancellationToken initialization."""
        token = CancellationToken()
        assert token.is_cancellation_requested is False
        assert token._request is None

    def test_cancellation_token_with_request(self):
        """Test CancellationToken with FastAPI request."""
        mock_request = MagicMock(spec=Request)
        token = CancellationToken(mock_request)
        assert token._request == mock_request
        assert token.is_cancellation_requested is False

    def test_cancellation_token_manual_cancel(self):
        """Test manual cancellation."""
        token = CancellationToken()
        token.cancel()
        assert token.is_cancellation_requested is True

    def test_throw_if_cancellation_requested_not_cancelled(self):
        """Test throw_if_cancellation_requested when not cancelled."""
        token = CancellationToken()
        # Should not raise exception
        token.throw_if_cancellation_requested()

    def test_throw_if_cancellation_requested_cancelled(self):
        """Test throw_if_cancellation_requested when cancelled."""
        token = CancellationToken()
        token.cancel()
        with pytest.raises(CancellationError, match="Operation was cancelled"):
            token.throw_if_cancellation_requested()

    @pytest.mark.asyncio
    async def test_wait_for_cancellation(self):
        """Test wait_for_cancellation."""
        token = CancellationToken()

        # Start waiting in background
        wait_task = asyncio.create_task(token.wait_for_cancellation())

        # Cancel after a short delay
        await asyncio.sleep(0.01)
        token.cancel()

        # Should complete
        await wait_task

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup method."""
        token = CancellationToken()
        await token.cleanup()
        # Should not raise any exception


class TestCancellationTokenFunctions:
    """Test cancellation token utility functions."""

    @pytest.mark.asyncio
    async def test_create_cancellation_token_context(self):
        """Test create_cancellation_token context manager."""
        async with create_cancellation_token() as token:
            assert isinstance(token, CancellationToken)
            assert token.is_cancellation_requested is False

    def test_get_cancellation_token(self):
        """Test get_cancellation_token function."""
        mock_request = MagicMock(spec=Request)
        token = get_cancellation_token(mock_request)
        assert isinstance(token, CancellationToken)
        assert token._request == mock_request

    def test_get_global_cancellation_token(self):
        """Test get_global_cancellation_token function."""
        token = get_global_cancellation_token()
        assert isinstance(token, CancellationToken)
        assert token._request is None


class TestHandlerRegistry:
    """Test HandlerRegistry class."""

    def test_handler_registry_initialization(self):
        """Test HandlerRegistry initialization."""
        registry = HandlerRegistry()
        assert registry.handlers == {}
        assert registry.logger is not None

    def test_register_handler(self):
        """Test handler registration."""
        registry = HandlerRegistry()
        handler = TestCommandHandler()

        registry.register_handler(TestCommand, handler)
        assert registry.handlers[TestCommand] == handler

    def test_get_handler(self):
        """Test getting registered handler."""
        registry = HandlerRegistry()
        handler = TestCommandHandler()

        registry.register_handler(TestCommand, handler)
        retrieved_handler = registry.get_handler(TestCommand)
        assert retrieved_handler == handler

    def test_get_handler_not_found(self):
        """Test getting non-existent handler."""
        registry = HandlerRegistry()
        handler = registry.get_handler(TestCommand)
        assert handler is None

    def test_clear_handlers(self):
        """Test clearing all handlers."""
        registry = HandlerRegistry()
        handler = TestCommandHandler()

        registry.register_handler(TestCommand, handler)
        assert len(registry.handlers) == 1

        registry.clear()
        assert len(registry.handlers) == 0

    def test_get_registered_types(self):
        """Test getting registered types."""
        registry = HandlerRegistry()
        handler = TestCommandHandler()

        registry.register_handler(TestCommand, handler)
        types = registry.get_registered_types()
        assert TestCommand in types


class TestPipelineBehaviors:
    """Test pipeline behaviors."""

    def test_behavior_wrapper_initialization(self):
        """Test BehaviorWrapper initialization."""
        behavior = TestBehavior("test")
        next_handler = MagicMock()
        wrapper = BehaviorWrapper(behavior, next_handler)

        assert wrapper.behavior == behavior
        assert wrapper.next_handler == next_handler

    @pytest.mark.asyncio
    async def test_behavior_wrapper_handle(self):
        """Test BehaviorWrapper handle method."""
        behavior = TestBehavior("test")
        next_handler = MagicMock()
        next_handler.handle = AsyncMock(return_value="result")

        wrapper = BehaviorWrapper(behavior, next_handler)
        token = CancellationToken()

        result = await wrapper.handle(TestCommand(name="test"), token)
        assert result == "test: result"
        assert behavior.called

    def test_validation_behavior_initialization(self):
        """Test ValidationBehavior initialization."""
        behavior = ValidationBehavior()
        assert behavior.logger is not None

    @pytest.mark.asyncio
    async def test_validation_behavior_with_valid_request(self):
        """Test ValidationBehavior with valid request."""
        behavior = ValidationBehavior()
        request = TestCommand(name="test")

        async def next_handler():
            return "success"

        result = await behavior.handle(request, next_handler)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_validation_behavior_with_invalid_request(self):
        """Test ValidationBehavior with invalid request."""
        behavior = ValidationBehavior()

        # Create a request that will fail validation by having invalid data
        class InvalidRequest(TestCommand):
            name: str

        # Create a request with invalid data that will cause validation to fail
        request = InvalidRequest(name="test")
        # Manually corrupt the request to cause validation failure
        request.name = None  # This should cause validation to fail

        async def next_handler():
            return "success"

        with pytest.raises(ValueError, match="Validation failed"):
            await behavior.handle(request, next_handler)

    def test_logging_behavior_initialization(self):
        """Test LoggingBehavior initialization."""
        behavior = LoggingBehavior()
        assert behavior.logger is not None

    @pytest.mark.asyncio
    async def test_logging_behavior_success(self):
        """Test LoggingBehavior with successful execution."""
        behavior = LoggingBehavior()
        request = TestCommand(name="test")

        async def next_handler():
            return "success"

        result = await behavior.handle(request, next_handler)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_logging_behavior_failure(self):
        """Test LoggingBehavior with failed execution."""
        behavior = LoggingBehavior()
        request = TestCommand(name="test")

        async def next_handler():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await behavior.handle(request, next_handler)

    @pytest.mark.asyncio
    async def test_logging_behavior_slow_execution(self):
        """Test LoggingBehavior with slow execution."""
        behavior = LoggingBehavior()
        request = TestCommand(name="test")

        async def next_handler():
            # Simulate slow execution
            await asyncio.sleep(0.01)
            return "success"

        result = await behavior.handle(request, next_handler)
        assert result == "success"


class TestMediator:
    """Test Mediator class."""

    def test_mediator_initialization(self):
        """Test Mediator initialization."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)

        assert mediator.handler_registry == registry
        assert mediator.logger is not None
        assert len(mediator.behaviors) == 2  # ValidationBehavior and LoggingBehavior

    @pytest.mark.asyncio
    async def test_send_command_success(self):
        """Test successful command sending."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)
        handler = TestCommandHandler()

        registry.register_handler(TestCommand, handler)
        token = CancellationToken()

        command = TestCommand(name="test")
        result = await mediator.send_command(command, token)

        assert result == "Command executed: test"

    @pytest.mark.asyncio
    async def test_send_query_success(self):
        """Test successful query sending."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)
        handler = TestQueryHandler()

        registry.register_handler(TestQuery, handler)
        token = CancellationToken()

        query = TestQuery(id="123")
        result = await mediator.send_query(query, token)

        assert result == "Query result: 123"

    @pytest.mark.asyncio
    async def test_send_without_handler(self):
        """Test sending request without registered handler."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)
        token = CancellationToken()

        command = TestCommand(name="test")

        with pytest.raises(ValueError, match="No handler registered for request type"):
            await mediator.send(command, token)

    @pytest.mark.asyncio
    async def test_register_handler(self):
        """Test registering handler through mediator."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)
        handler = TestCommandHandler()

        mediator.register_handler(TestCommand, handler)
        assert registry.get_handler(TestCommand) == handler

    def test_register_behavior(self):
        """Test registering pipeline behavior."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)
        behavior = TestBehavior("custom")

        initial_count = len(mediator.behaviors)
        mediator.register_behavior(behavior)
        assert len(mediator.behaviors) == initial_count + 1
        assert behavior in mediator.behaviors

    @pytest.mark.asyncio
    async def test_pipeline_execution_order(self):
        """Test pipeline execution order."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)
        handler = TestCommandHandler()

        # Add custom behavior
        custom_behavior = TestBehavior("custom")
        mediator.register_behavior(custom_behavior)

        registry.register_handler(TestCommand, handler)
        token = CancellationToken()

        command = TestCommand(name="test")
        result = await mediator.send(command, token)

        # Should execute through all behaviors
        assert "custom:" in result
        assert "Command executed: test" in result

    @pytest.mark.asyncio
    async def test_mediator_with_cancellation(self):
        """Test mediator with cancellation token."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)
        handler = TestCommandHandler()

        registry.register_handler(TestCommand, handler)
        token = CancellationToken()

        # Cancel the token
        token.cancel()

        command = TestCommand(name="test")

        # Should still execute (cancellation is checked by handlers)
        result = await mediator.send(command, token)
        assert result == "Command executed: test"


class TestMediatorIntegration:
    """Integration tests for mediator pattern."""

    @pytest.mark.asyncio
    async def test_full_mediator_workflow(self):
        """Test complete mediator workflow."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)

        # Register handlers
        command_handler = TestCommandHandler()
        query_handler = TestQueryHandler()

        registry.register_handler(TestCommand, command_handler)
        registry.register_handler(TestQuery, query_handler)

        token = CancellationToken()

        # Test command
        command = TestCommand(name="integration_test")
        command_result = await mediator.send_command(command, token)
        assert command_result == "Command executed: integration_test"

        # Test query
        query = TestQuery(id="integration_123")
        query_result = await mediator.send_query(query, token)
        assert query_result == "Query result: integration_123"

    @pytest.mark.asyncio
    async def test_mediator_with_multiple_behaviors(self):
        """Test mediator with multiple pipeline behaviors."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)
        handler = TestCommandHandler()

        # Add multiple custom behaviors
        behavior1 = TestBehavior("behavior1")
        behavior2 = TestBehavior("behavior2")

        mediator.register_behavior(behavior1)
        mediator.register_behavior(behavior2)

        registry.register_handler(TestCommand, handler)
        token = CancellationToken()

        command = TestCommand(name="multi_behavior_test")
        result = await mediator.send(command, token)

        # Should execute through all behaviors in order
        assert "behavior1:" in result
        assert "behavior2:" in result
        assert "Command executed: multi_behavior_test" in result

    @pytest.mark.asyncio
    async def test_mediator_error_handling(self):
        """Test mediator error handling."""
        registry = HandlerRegistry()
        mediator = Mediator(registry)

        # Create a handler that raises an exception
        class FailingHandler(IRequestHandler[TestCommand, str]):
            async def handle(
                self,
                request: TestCommand,
                cancellation_token: CancellationToken,  # noqa: ARG002
            ) -> str:
                raise ValueError("Handler failed")

        handler = FailingHandler()
        registry.register_handler(TestCommand, handler)
        token = CancellationToken()

        command = TestCommand(name="error_test")

        with pytest.raises(ValueError, match="Handler failed"):
            await mediator.send(command, token)


class TestCancellationError:
    """Test CancellationError exception."""

    def test_cancellation_error_creation(self):
        """Test CancellationError creation."""
        error = CancellationError("Test cancellation")
        assert str(error) == "Test cancellation"
