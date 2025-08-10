"""Tests for the contracts CQRS module."""

# type: ignore[misc,func-returns-value]

from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from eshop.core.contracts.cqrs import (
    ICommand,
    ICommandHandler,
    ICommandHandlerNoResponse,
    ICommandNoResponse,
    IQuery,
    IQueryHandler,
)


@pytest.mark.no_collect
class TestCommand(ICommand[str]):
    """Test command implementation."""

    name: str
    value: int


@pytest.mark.no_collect
class TestCommandNoResponse(ICommandNoResponse):
    """Test command with no response implementation."""

    name: str
    value: int


@pytest.mark.no_collect
class TestQuery(IQuery[str]):
    """Test query implementation."""

    name: str
    value: int


@pytest.mark.no_collect
class TestCommandHandler(ICommandHandler[TestCommand, str]):
    """Test command handler implementation."""

    async def handle(self, command: TestCommand) -> str:
        return f"Processed {command.name} with value {command.value}"  # type: ignore


@pytest.mark.no_collect
class TestCommandHandlerNoResponse(ICommandHandlerNoResponse[TestCommandNoResponse]):
    """Test command handler with no response implementation."""

    async def handle(self, command: TestCommandNoResponse) -> None:
        # Simulate processing without return value
        pass  # noqa: ARG001


@pytest.mark.no_collect
class TestQueryHandler(IQueryHandler[TestQuery, str]):
    """Test query handler implementation."""

    async def handle(self, query: TestQuery) -> str:
        return f"Retrieved {query.name} with value {query.value}"


class TestICommand:
    """Test ICommand interface."""

    def test_command_creation(self) -> None:
        """Test command creation and inheritance."""
        command = TestCommand(name="test", value=42)

        assert isinstance(command, ICommand)
        assert isinstance(command, BaseModel)
        assert command.name == "test"
        assert command.value == 42

    def test_command_serialization(self) -> None:
        """Test command serialization."""
        command = TestCommand(name="test", value=42)

        command_dict = command.model_dump()
        assert command_dict["name"] == "test"
        assert command_dict["value"] == 42

        command_json = command.model_dump_json()
        assert "test" in command_json
        assert "42" in command_json

    def test_command_validation(self) -> None:
        """Test command validation."""
        # Valid command
        command = TestCommand(name="test", value=42)
        assert command.name == "test"
        assert command.value == 42

    def test_command_inheritance(self) -> None:
        """Test command inheritance from BaseModel."""
        command = TestCommand(name="test", value=42)

        assert isinstance(command, BaseModel)
        assert hasattr(command, "model_dump")
        assert hasattr(command, "model_dump_json")

    def test_command_generic_type(self) -> None:
        """Test command generic type parameter."""
        command = TestCommand(name="test", value=42)

        # Test that it's properly typed as ICommand
        assert isinstance(command, ICommand)
        # Test that it has generic type support
        assert hasattr(command, "__orig_bases__")


class TestICommandNoResponse:
    """Test ICommandNoResponse interface."""

    def test_command_no_response_creation(self) -> None:
        """Test command with no response creation."""
        command = TestCommandNoResponse(name="test", value=42)

        assert isinstance(command, ICommandNoResponse)
        assert isinstance(command, ICommand)
        assert isinstance(command, BaseModel)
        assert command.name == "test"
        assert command.value == 42

    def test_command_no_response_inheritance(self) -> None:
        """Test command with no response inheritance."""
        command = TestCommandNoResponse(name="test", value=42)

        assert isinstance(command, ICommandNoResponse)
        assert isinstance(command, ICommand[None])  # type: ignore
        assert isinstance(command, BaseModel)

    def test_command_no_response_serialization(self) -> None:
        """Test command with no response serialization."""
        command = TestCommandNoResponse(name="test", value=42)

        command_dict = command.model_dump()
        assert command_dict["name"] == "test"
        assert command_dict["value"] == 42


class TestIQuery:
    """Test IQuery interface."""

    def test_query_creation(self) -> None:
        """Test query creation and inheritance."""
        query = TestQuery(name="test", value=42)

        assert isinstance(query, IQuery)
        assert isinstance(query, BaseModel)
        assert query.name == "test"
        assert query.value == 42

    def test_query_serialization(self) -> None:
        """Test query serialization."""
        query = TestQuery(name="test", value=42)

        query_dict = query.model_dump()
        assert query_dict["name"] == "test"
        assert query_dict["value"] == 42

        query_json = query.model_dump_json()
        assert "test" in query_json
        assert "42" in query_json

    def test_query_validation(self) -> None:
        """Test query validation."""
        # Valid query
        query = TestQuery(name="test", value=42)
        assert query.name == "test"
        assert query.value == 42

    def test_query_inheritance(self) -> None:
        """Test query inheritance from BaseModel."""
        query = TestQuery(name="test", value=42)

        assert isinstance(query, BaseModel)
        assert hasattr(query, "model_dump")
        assert hasattr(query, "model_dump_json")

    def test_query_generic_type(self) -> None:
        """Test query generic type parameter."""
        query = TestQuery(name="test", value=42)

        # Test that it's properly typed as IQuery
        assert isinstance(query, IQuery)
        # Test that it has generic type support
        assert hasattr(query, "__orig_bases__")


class TestICommandHandler:
    """Test ICommandHandler interface."""

    def test_command_handler_interface(self) -> None:
        """Test ICommandHandler interface definition."""
        # This test ensures the interface is properly defined
        assert hasattr(ICommandHandler, "handle")

        # Test that it's an abstract method
        with pytest.raises(TypeError):
            ICommandHandler()  # type: ignore

    @pytest.mark.asyncio
    async def test_command_handler_implementation(self) -> None:
        """Test command handler implementation."""
        handler = TestCommandHandler()
        command = TestCommand(name="test", value=42)

        result = await handler.handle(command)

        assert isinstance(result, str)
        assert result == "Processed test with value 42"

    @pytest.mark.asyncio
    async def test_command_handler_with_mock(self) -> None:
        """Test command handler with mock implementation."""
        mock_handler = AsyncMock(spec=ICommandHandler[TestCommand, str])
        command = TestCommand(name="test", value=42)
        mock_handler.handle.return_value = "Mock result"

        result = await mock_handler.handle(command)

        assert result == "Mock result"
        mock_handler.handle.assert_called_once_with(command)

    def test_command_handler_generic_types(self) -> None:
        """Test command handler generic type parameters."""
        handler = TestCommandHandler()

        # Check that it's properly typed
        assert hasattr(handler, "__orig_bases__")
        # The handler should be typed as ICommandHandler[TestCommand, str]
        assert ICommandHandler[TestCommand, str] in handler.__class__.__orig_bases__  # type: ignore


class TestICommandHandlerNoResponse:
    """Test ICommandHandlerNoResponse interface."""

    def test_command_handler_no_response_interface(self) -> None:
        """Test ICommandHandlerNoResponse interface definition."""
        # This test ensures the interface is properly defined
        assert hasattr(ICommandHandlerNoResponse, "handle")

        # Test that it's an abstract method
        with pytest.raises(TypeError):
            ICommandHandlerNoResponse()  # type: ignore

    @pytest.mark.asyncio
    async def test_command_handler_no_response_implementation(self) -> None:
        """Test command handler with no response implementation."""
        handler = TestCommandHandlerNoResponse()
        command = TestCommandNoResponse(name="test", value=42)

        result = await handler.handle(command)

        assert result is None

    @pytest.mark.asyncio
    async def test_command_handler_no_response_with_mock(self) -> None:
        """Test command handler with no response using mock."""
        mock_handler = AsyncMock(spec=ICommandHandlerNoResponse[TestCommandNoResponse])
        command = TestCommandNoResponse(name="test", value=42)
        mock_handler.handle.return_value = None

        result = await mock_handler.handle(command)

        assert result is None
        mock_handler.handle.assert_called_once_with(command)

    def test_command_handler_no_response_generic_types(self) -> None:
        """Test command handler with no response generic type parameters."""
        handler = TestCommandHandlerNoResponse()

        # Check that it's properly typed
        assert hasattr(handler, "__orig_bases__")
        # The handler should be typed as ICommandHandlerNoResponse[TestCommandNoResponse]
        assert (
            ICommandHandlerNoResponse[TestCommandNoResponse]
            in handler.__class__.__orig_bases__  # type: ignore
        )


class TestIQueryHandler:
    """Test IQueryHandler interface."""

    def test_query_handler_interface(self) -> None:
        """Test IQueryHandler interface definition."""
        # This test ensures the interface is properly defined
        assert hasattr(IQueryHandler, "handle")

        # Test that it's an abstract method
        with pytest.raises(TypeError):
            IQueryHandler()  # type: ignore

    @pytest.mark.asyncio
    async def test_query_handler_implementation(self) -> None:
        """Test query handler implementation."""
        handler = TestQueryHandler()
        query = TestQuery(name="test", value=42)

        result = await handler.handle(query)

        assert isinstance(result, str)
        assert result == "Retrieved test with value 42"

    @pytest.mark.asyncio
    async def test_query_handler_with_mock(self) -> None:
        """Test query handler with mock implementation."""
        mock_handler = AsyncMock(spec=IQueryHandler[TestQuery, str])
        query = TestQuery(name="test", value=42)
        mock_handler.handle.return_value = "Mock result"

        result = await mock_handler.handle(query)

        assert result == "Mock result"
        mock_handler.handle.assert_called_once_with(query)

    def test_query_handler_generic_types(self) -> None:
        """Test query handler generic type parameters."""
        handler = TestQueryHandler()

        # Check that it's properly typed
        assert hasattr(handler, "__orig_bases__")
        # The handler should be typed as IQueryHandler[TestQuery, str]
        assert IQueryHandler[TestQuery, str] in handler.__class__.__orig_bases__  # type: ignore


class TestCQRSContractsIntegration:
    """Integration tests for CQRS contracts."""

    @pytest.mark.asyncio
    async def test_complete_command_flow(self) -> None:
        """Test complete command flow with handler."""
        # Create command and handler
        command = TestCommand(name="test_command", value=100)
        handler = TestCommandHandler()

        # Execute command
        result = await handler.handle(command)

        # Verify result
        assert isinstance(result, str)
        assert "test_command" in result
        assert "100" in result

    @pytest.mark.asyncio
    async def test_complete_query_flow(self) -> None:
        """Test complete query flow with handler."""
        # Create query and handler
        query = TestQuery(name="test_query", value=200)
        handler = TestQueryHandler()

        # Execute query
        result = await handler.handle(query)

        # Verify result
        assert isinstance(result, str)
        assert "test_query" in result
        assert "200" in result

    @pytest.mark.asyncio
    async def test_command_no_response_flow(self) -> None:
        """Test command with no response flow."""
        # Create command and handler
        command = TestCommandNoResponse(name="test_command", value=300)
        handler = TestCommandHandlerNoResponse()

        # Execute command
        result = await handler.handle(command)

        # Verify result is None
        assert result is None

    def test_command_query_distinction(self) -> None:
        """Test that commands and queries are distinct types."""
        command = TestCommand(name="test", value=42)
        query = TestQuery(name="test", value=42)

        # They should be different types
        assert isinstance(command, ICommand)
        assert isinstance(query, IQuery)
        assert not isinstance(command, IQuery)
        assert not isinstance(query, ICommand)

    def test_handler_type_safety(self) -> None:
        """Test handler type safety."""
        command_handler = TestCommandHandler()
        query_handler = TestQueryHandler()

        # They should be different types
        assert isinstance(command_handler, ICommandHandler)
        assert isinstance(query_handler, IQueryHandler)
        assert not isinstance(command_handler, IQueryHandler)
        assert not isinstance(query_handler, ICommandHandler)

    def test_serialization_consistency(self) -> None:
        """Test that commands and queries serialize consistently."""
        command = TestCommand(name="test", value=42)
        query = TestQuery(name="test", value=42)

        command_dict = command.model_dump()
        query_dict = query.model_dump()

        # They should have the same structure
        assert command_dict == query_dict
        assert command_dict["name"] == "test"
        assert command_dict["value"] == 42

    def test_pydantic_configuration(self) -> None:
        """Test that Pydantic configuration is properly set."""
        command = TestCommand(name="test", value=42)
        query = TestQuery(name="test", value=42)

        # Both should have arbitrary_types_allowed enabled
        assert command.model_config.get("arbitrary_types_allowed", False) is True
        assert query.model_config.get("arbitrary_types_allowed", False) is True

    def test_complex_data_types(self) -> None:
        """Test commands and queries with complex data types."""

        @pytest.mark.no_collect
        class ComplexCommand(ICommand[dict[str, Any]]):
            id: UUID
            data: dict[str, Any]
            tags: list[str]

        @pytest.mark.no_collect
        class ComplexQuery(IQuery[list[dict[str, Any]]]):
            filter: dict[str, Any]
            limit: int
            offset: int

        # Test complex command
        command = ComplexCommand(
            id=uuid4(),
            data={"key": "value", "nested": {"inner": "data"}},
            tags=["tag1", "tag2"],
        )

        assert isinstance(command.id, UUID)
        assert command.data["key"] == "value"
        assert command.data["nested"]["inner"] == "data"
        assert command.tags == ["tag1", "tag2"]

        # Test complex query
        query = ComplexQuery(
            filter={"status": "active", "category": "test"}, limit=10, offset=0
        )

        assert query.filter["status"] == "active"
        assert query.filter["category"] == "test"
        assert query.limit == 10
        assert query.offset == 0

    def test_inheritance_hierarchy(self) -> None:
        """Test the inheritance hierarchy of CQRS contracts."""
        command = TestCommand(name="test", value=42)
        command_no_response = TestCommandNoResponse(name="test", value=42)
        query = TestQuery(name="test", value=42)

        # Test inheritance relationships
        assert isinstance(command, ICommand)
        assert isinstance(command_no_response, ICommand)
        assert isinstance(command_no_response, ICommandNoResponse)
        assert isinstance(query, IQuery)

        # Test that they inherit from BaseModel
        assert isinstance(command, BaseModel)
        assert isinstance(command_no_response, BaseModel)
        assert isinstance(query, BaseModel)

    def test_type_variables(self) -> None:
        """Test type variable usage in CQRS contracts."""
        # Test that type variables are properly used
        assert hasattr(ICommand, "__parameters__")
        assert hasattr(IQuery, "__parameters__")
        assert hasattr(ICommandHandler, "__parameters__")
        assert hasattr(IQueryHandler, "__parameters__")

        # Test that they have the expected number of type parameters
        assert len(ICommand.__parameters__) == 1  # TResponse
        assert len(IQuery.__parameters__) == 1  # TResponse
        assert len(ICommandHandler.__parameters__) == 2  # TCommand, TResponse
        assert len(IQueryHandler.__parameters__) == 2  # TQuery, TResponse
