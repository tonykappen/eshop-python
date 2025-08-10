"""Tests for the CQRS base module."""

# type: ignore

from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from eshop.core.cqrs.base import (
    CommandResult,
    ICommand,
    ICommandHandler,
    IQuery,
    IQueryHandler,
    QueryResult,
)


@pytest.mark.no_collect
class TestCommand(ICommand):
    """Test command implementation."""

    name: str
    value: int


@pytest.mark.no_collect
class TestQuery(IQuery):
    """Test query implementation."""

    name: str
    value: int


@pytest.mark.no_collect
class TestResult(BaseModel):
    """Test result implementation."""

    id: UUID
    name: str
    value: int


@pytest.mark.no_collect
class TestCommandHandler(ICommandHandler[TestResult]):
    """Test command handler implementation."""

    async def handle(self, command: ICommand) -> TestResult:
        # Type cast to access attributes
        cmd = command  # type: ignore
        return TestResult(
            id=uuid4(), name=f"Processed {command.name}", value=command.value * 2  # type: ignore
        )


@pytest.mark.no_collect
class TestQueryHandler(IQueryHandler[TestResult]):
    """Test query handler implementation."""

    async def handle(self, query: IQuery) -> TestResult:
        # Type cast to access attributes
        qry = query  # type: ignore
        return TestResult(id=uuid4(), name=f"Retrieved {query.name}", value=query.value)  # type: ignore


class TestICommand:
    """Test ICommand interface."""

    def test_command_creation(self) -> None:
        """Test command creation and inheritance."""
        command = TestCommand(name="test", value=42)

        assert isinstance(command, ICommand)  # type: ignore
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


class TestIQuery:
    """Test IQuery interface."""

    def test_query_creation(self) -> None:
        """Test query creation and inheritance."""
        query = TestQuery(name="test", value=42)

        assert isinstance(query, IQuery)  # type: ignore
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

        assert isinstance(result, TestResult)
        assert result.name == "Processed test"
        assert result.value == 84  # 42 * 2

    @pytest.mark.asyncio
    async def test_command_handler_with_mock(self) -> None:
        """Test command handler with mock implementation."""
        mock_handler = AsyncMock(spec=ICommandHandler[TestResult])
        command = TestCommand(name="test", value=42)
        mock_result = TestResult(id=uuid4(), name="Mock result", value=100)
        mock_handler.handle.return_value = mock_result

        result = await mock_handler.handle(command)

        assert result == mock_result
        mock_handler.handle.assert_called_once_with(command)

    def test_command_handler_generic_types(self) -> None:
        """Test command handler generic type parameters."""
        handler = TestCommandHandler()

        # Check that it's properly typed
        assert hasattr(handler, "__orig_bases__")
        # The handler should be typed as ICommandHandler[TestResult]
        assert ICommandHandler[TestResult] in handler.__class__.__orig_bases__


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

        assert isinstance(result, TestResult)
        assert result.name == "Retrieved test"
        assert result.value == 42

    @pytest.mark.asyncio
    async def test_query_handler_with_mock(self) -> None:
        """Test query handler with mock implementation."""
        mock_handler = AsyncMock(spec=IQueryHandler[TestResult])
        query = TestQuery(name="test", value=42)
        mock_result = TestResult(id=uuid4(), name="Mock result", value=100)
        mock_handler.handle.return_value = mock_result

        result = await mock_handler.handle(query)

        assert result == mock_result
        mock_handler.handle.assert_called_once_with(query)

    def test_query_handler_generic_types(self) -> None:
        """Test query handler generic type parameters."""
        handler = TestQueryHandler()

        # Check that it's properly typed
        assert hasattr(handler, "__orig_bases__")
        # The handler should be typed as IQueryHandler[TestResult]
        assert IQueryHandler[TestResult] in handler.__class__.__orig_bases__


class TestCommandResult:
    """Test CommandResult class."""

    def test_command_result_default_values(self) -> None:
        """Test CommandResult with default values."""
        result = CommandResult(success=True)

        assert result.success is True
        assert result.message == ""
        assert result.data is None

    def test_command_result_custom_values(self) -> None:
        """Test CommandResult with custom values."""
        data = {"key": "value", "number": 42}
        result = CommandResult(success=False, message="Operation failed", data=data)

        assert result.success is False
        assert result.message == "Operation failed"
        assert result.data == data

    def test_command_result_serialization(self) -> None:
        """Test CommandResult serialization."""
        result = CommandResult(
            success=True, message="Operation successful", data={"id": 123}
        )

        result_dict = result.model_dump()
        assert result_dict["success"] is True
        assert result_dict["message"] == "Operation successful"
        assert result_dict["data"]["id"] == 123

    def test_command_result_with_complex_data(self) -> None:
        """Test CommandResult with complex data types."""
        complex_data = {
            "id": uuid4(),
            "items": ["item1", "item2"],
            "metadata": {"created": "2023-01-01", "version": 1.0},
        }

        result = CommandResult(
            success=True, message="Complex operation completed", data=complex_data
        )

        assert result.success is True
        assert result.message == "Complex operation completed"
        assert result.data["id"] == complex_data["id"]
        assert result.data["items"] == ["item1", "item2"]
        assert result.data["metadata"]["version"] == 1.0

    def test_command_result_validation(self) -> None:
        """Test CommandResult validation."""
        # Valid result
        result = CommandResult(success=True)
        assert result.success is True

        # Valid result with data
        result = CommandResult(success=False, data={"error": "test"})
        assert result.success is False
        assert result.data["error"] == "test"


class TestQueryResult:
    """Test QueryResult class."""

    def test_query_result_creation(self) -> None:
        """Test QueryResult creation."""
        data = TestResult(id=uuid4(), name="test", value=42)
        result = QueryResult[TestResult](
            success=True, data=data, message="Query successful"
        )

        assert result.success is True
        assert result.data == data
        assert result.message == "Query successful"

    def test_query_result_serialization(self) -> None:
        """Test QueryResult serialization."""
        data = TestResult(id=uuid4(), name="test", value=42)
        result = QueryResult[TestResult](
            success=True, data=data, message="Query successful"
        )

        result_dict = result.model_dump()
        assert result_dict["success"] is True
        assert result_dict["data"]["name"] == "test"
        assert result_dict["data"]["value"] == 42
        assert result_dict["message"] == "Query successful"

    def test_query_result_with_primitive_data(self) -> None:
        """Test QueryResult with primitive data types."""
        # Test with string data
        result = QueryResult[str](
            success=True, data="test string", message="String query"
        )

        assert result.success is True
        assert result.data == "test string"
        assert result.message == "String query"

        # Test with integer data
        result_int: QueryResult[int] = QueryResult[int](success=True, data=42, message="Integer query")

        assert result_int.success is True
        assert result_int.data == 42
        assert result_int.message == "Integer query"

    def test_query_result_with_list_data(self) -> None:
        """Test QueryResult with list data."""
        data = [
            TestResult(id=uuid4(), name="item1", value=1),
            TestResult(id=uuid4(), name="item2", value=2),
        ]

        result = QueryResult[list[TestResult]](
            success=True, data=data, message="List query"
        )

        assert result.success is True
        assert len(result.data) == 2
        assert result.data[0].name == "item1"
        assert result.data[1].name == "item2"
        assert result.message == "List query"

    def test_query_result_validation(self) -> None:
        """Test QueryResult validation."""
        # Valid result
        data = TestResult(id=uuid4(), name="test", value=42)
        result = QueryResult[TestResult](success=True, data=data)
        assert result.success is True
        assert result.data == data

        # Valid result with message
        result = QueryResult[TestResult](
            success=False, data=data, message="Query failed"
        )
        assert result.success is False
        assert result.message == "Query failed"

    def test_query_result_generic_type_safety(self) -> None:
        """Test QueryResult generic type safety."""
        # Test that the generic type is properly enforced
        data = TestResult(id=uuid4(), name="test", value=42)
        result = QueryResult[TestResult](success=True, data=data)

        # Test that it's properly typed as QueryResult
        assert isinstance(result, QueryResult)  # type: ignore
        # Test that it has generic type support
        assert hasattr(result, "__orig_bases__")


class TestCQRSBaseIntegration:
    """Integration tests for CQRS base functionality."""

    @pytest.mark.asyncio
    async def test_complete_command_flow(self) -> None:
        """Test complete command flow with handler and result."""
        # Create command and handler
        command = TestCommand(name="test_command", value=50)
        handler = TestCommandHandler()

        # Execute command
        result = await handler.handle(command)

        # Verify result
        assert isinstance(result, TestResult)
        assert result.name == "Processed test_command"
        assert result.value == 100  # 50 * 2

    @pytest.mark.asyncio
    async def test_complete_query_flow(self) -> None:
        """Test complete query flow with handler and result."""
        # Create query and handler
        query = TestQuery(name="test_query", value=75)
        handler = TestQueryHandler()

        # Execute query
        result = await handler.handle(query)

        # Verify result
        assert isinstance(result, TestResult)
        assert result.name == "Retrieved test_query"
        assert result.value == 75

    def test_command_query_distinction(self) -> None:
        """Test that commands and queries are distinct types."""
        command = TestCommand(name="test", value=42)
        query = TestQuery(name="test", value=42)

        # They should be different types
        assert isinstance(command, ICommand)  # type: ignore
        assert isinstance(query, IQuery)  # type: ignore
        assert not isinstance(command, IQuery)  # type: ignore
        assert not isinstance(query, ICommand)  # type: ignore

    def test_handler_type_safety(self) -> None:
        """Test handler type safety."""
        command_handler = TestCommandHandler()
        query_handler = TestQueryHandler()

        # They should be different types
        assert isinstance(command_handler, ICommandHandler)
        assert isinstance(query_handler, IQueryHandler)
        assert not isinstance(command_handler, IQueryHandler)
        assert not isinstance(query_handler, ICommandHandler)

    def test_result_type_safety(self) -> None:
        """Test result type safety."""
        # Test CommandResult
        command_result = CommandResult(success=True, data={"key": "value"})
        assert isinstance(command_result, CommandResult)
        assert command_result.success is True
        assert command_result.data["key"] == "value"

        # Test QueryResult
        query_data = TestResult(id=uuid4(), name="test", value=42)
        query_result = QueryResult[TestResult](success=True, data=query_data)
        assert isinstance(query_result, QueryResult)
        assert query_result.success is True
        assert query_result.data == query_data

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
        class ComplexCommand(ICommand):
            id: UUID
            data: dict[str, Any]
            tags: list[str]

        @pytest.mark.no_collect
        class ComplexQuery(IQuery):
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
        """Test the inheritance hierarchy of CQRS base classes."""
        command = TestCommand(name="test", value=42)
        query = TestQuery(name="test", value=42)

        # Test inheritance relationships
        assert isinstance(command, ICommand)  # type: ignore
        assert isinstance(query, IQuery)  # type: ignore

        # Test that they inherit from BaseModel
        assert isinstance(command, BaseModel)
        assert isinstance(query, BaseModel)

    def test_backward_compatibility(self) -> None:
        """Test backward compatibility aliases."""
        # Test that ICommand and IQuery are properly aliased
        from eshop.core.contracts.cqrs import ICommand as ICommandContract
        from eshop.core.contracts.cqrs import IQuery as IQueryContract

        command = TestCommand(name="test", value=42)
        query = TestQuery(name="test", value=42)

        # They should be compatible with the contract versions
        assert isinstance(command, ICommandContract)  # type: ignore
        assert isinstance(query, IQueryContract)  # type: ignore

    def test_result_workflow(self) -> None:
        """Test complete result workflow."""
        # Test CommandResult workflow
        command_data = {"operation": "create", "entity": "user"}
        command_result = CommandResult(
            success=True, message="User created successfully", data=command_data
        )

        assert command_result.success is True
        assert command_result.message == "User created successfully"
        assert command_result.data["operation"] == "create"

        # Test QueryResult workflow
        query_data = TestResult(id=uuid4(), name="user", value=1)
        query_result = QueryResult[TestResult](
            success=True, data=query_data, message="User retrieved successfully"
        )

        assert query_result.success is True
        assert query_result.data == query_data
        assert query_result.message == "User retrieved successfully"

    def test_error_handling_workflow(self) -> None:
        """Test error handling workflow with results."""
        # Test CommandResult with error
        error_data = {"error_code": "VALIDATION_ERROR", "details": "Invalid input"}
        command_result = CommandResult(
            success=False, message="Command failed", data=error_data
        )

        assert command_result.success is False
        assert command_result.message == "Command failed"
        assert command_result.data["error_code"] == "VALIDATION_ERROR"

        # Test QueryResult with error
        query_result = QueryResult[str](success=False, data="", message="Query failed")

        assert query_result.success is False
        assert query_result.message == "Query failed"
