"""Comprehensive tests for the CQRS contracts."""

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


class TestICommand:
    """Test ICommand interface."""

    def test_icommand_inheritance(self):
        """Test that ICommand inherits from BaseModel."""
        assert issubclass(ICommand, BaseModel)

    def test_icommand_generic_type(self):
        """Test ICommand generic type parameter."""
        class TestCommand(ICommand[str]):
            name: str
        
        command = TestCommand(name="test")
        assert command.name == "test"
        assert isinstance(command, ICommand)

    def test_icommand_config(self):
        """Test ICommand configuration."""
        assert hasattr(ICommand, 'Config')
        assert hasattr(ICommand.Config, 'arbitrary_types_allowed')
        assert ICommand.Config.arbitrary_types_allowed is True


class TestICommandNoResponse:
    """Test ICommandNoResponse interface."""

    def test_icommand_no_response_inheritance(self):
        """Test that ICommandNoResponse inherits from ICommand."""
        assert issubclass(ICommandNoResponse, ICommand)

    def test_icommand_no_response_generic_type(self):
        """Test ICommandNoResponse has None as response type."""
        class TestCommand(ICommandNoResponse):
            name: str
        
        command = TestCommand(name="test")
        assert command.name == "test"
        assert isinstance(command, ICommandNoResponse)
        assert isinstance(command, ICommand)


class TestIQuery:
    """Test IQuery interface."""

    def test_iquery_inheritance(self):
        """Test that IQuery inherits from BaseModel."""
        assert issubclass(IQuery, BaseModel)

    def test_iquery_generic_type(self):
        """Test IQuery generic type parameter."""
        class TestQuery(IQuery[str]):
            id: str
        
        query = TestQuery(id="123")
        assert query.id == "123"
        assert isinstance(query, IQuery)

    def test_iquery_config(self):
        """Test IQuery configuration."""
        assert hasattr(IQuery, 'Config')
        assert hasattr(IQuery.Config, 'arbitrary_types_allowed')
        assert IQuery.Config.arbitrary_types_allowed is True


class TestICommandHandler:
    """Test ICommandHandler interface."""

    def test_icommand_handler_abstract_method(self):
        """Test that ICommandHandler has abstract handle method."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            ICommandHandler()

    def test_icommand_handler_implementation(self):
        """Test ICommandHandler implementation."""
        class TestCommand(ICommand[str]):
            name: str

        class TestCommandHandler(ICommandHandler[TestCommand, str]):
            async def handle(self, command: TestCommand) -> str:
                return f"Handled: {command.name}"

        handler = TestCommandHandler()
        assert isinstance(handler, ICommandHandler)

    @pytest.mark.asyncio
    async def test_icommand_handler_usage(self):
        """Test ICommandHandler usage."""
        class TestCommand(ICommand[str]):
            name: str

        class TestCommandHandler(ICommandHandler[TestCommand, str]):
            async def handle(self, command: TestCommand) -> str:
                return f"Handled: {command.name}"

        handler = TestCommandHandler()
        command = TestCommand(name="test")
        result = await handler.handle(command)
        assert result == "Handled: test"


class TestICommandHandlerNoResponse:
    """Test ICommandHandlerNoResponse interface."""

    def test_icommand_handler_no_response_abstract_method(self):
        """Test that ICommandHandlerNoResponse has abstract handle method."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            ICommandHandlerNoResponse()

    def test_icommand_handler_no_response_implementation(self):
        """Test ICommandHandlerNoResponse implementation."""
        class TestCommand(ICommandNoResponse):
            name: str

        class TestCommandHandler(ICommandHandlerNoResponse[TestCommand]):
            async def handle(self, command: TestCommand) -> None:
                # Do something with command
                pass

        handler = TestCommandHandler()
        assert isinstance(handler, ICommandHandlerNoResponse)

    @pytest.mark.asyncio
    async def test_icommand_handler_no_response_usage(self):
        """Test ICommandHandlerNoResponse usage."""
        class TestCommand(ICommandNoResponse):
            name: str

        class TestCommandHandler(ICommandHandlerNoResponse[TestCommand]):
            def __init__(self):
                self.processed = False

            async def handle(self, command: TestCommand) -> None:
                self.processed = True

        handler = TestCommandHandler()
        command = TestCommand(name="test")
        result = await handler.handle(command)
        assert result is None
        assert handler.processed is True


class TestIQueryHandler:
    """Test IQueryHandler interface."""

    def test_iquery_handler_abstract_method(self):
        """Test that IQueryHandler has abstract handle method."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            IQueryHandler()

    def test_iquery_handler_implementation(self):
        """Test IQueryHandler implementation."""
        class TestQuery(IQuery[str]):
            id: str

        class TestQueryHandler(IQueryHandler[TestQuery, str]):
            async def handle(self, query: TestQuery) -> str:
                return f"Query result: {query.id}"

        handler = TestQueryHandler()
        assert isinstance(handler, IQueryHandler)

    @pytest.mark.asyncio
    async def test_iquery_handler_usage(self):
        """Test IQueryHandler usage."""
        class TestQuery(IQuery[str]):
            id: str

        class TestQueryHandler(IQueryHandler[TestQuery, str]):
            async def handle(self, query: TestQuery) -> str:
                return f"Query result: {query.id}"

        handler = TestQueryHandler()
        query = TestQuery(id="123")
        result = await handler.handle(query)
        assert result == "Query result: 123"


class TestCQRSIntegration:
    """Integration tests for CQRS contracts."""

    @pytest.mark.asyncio
    async def test_command_handler_integration(self):
        """Test complete command handler integration."""
        class CreateUserCommand(ICommand[str]):
            name: str
            email: str

        class CreateUserHandler(ICommandHandler[CreateUserCommand, str]):
            async def handle(self, command: CreateUserCommand) -> str:
                return f"User created: {command.name} ({command.email})"

        handler = CreateUserHandler()
        command = CreateUserCommand(name="John Doe", email="john@example.com")
        result = await handler.handle(command)
        assert result == "User created: John Doe (john@example.com)"

    @pytest.mark.asyncio
    async def test_query_handler_integration(self):
        """Test complete query handler integration."""
        class GetUserQuery(IQuery[dict]):
            user_id: str

        class GetUserHandler(IQueryHandler[GetUserQuery, dict]):
            async def handle(self, query: GetUserQuery) -> dict:
                return {
                    "id": query.user_id,
                    "name": "John Doe",
                    "email": "john@example.com"
                }

        handler = GetUserHandler()
        query = GetUserQuery(user_id="123")
        result = await handler.handle(query)
        assert result["id"] == "123"
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_command_no_response_integration(self):
        """Test command with no response integration."""
        class DeleteUserCommand(ICommandNoResponse):
            user_id: str

        class DeleteUserHandler(ICommandHandlerNoResponse[DeleteUserCommand]):
            def __init__(self):
                self.deleted_users = []

            async def handle(self, command: DeleteUserCommand) -> None:
                self.deleted_users.append(command.user_id)

        handler = DeleteUserHandler()
        command = DeleteUserCommand(user_id="123")
        result = await handler.handle(command)
        assert result is None
        assert "123" in handler.deleted_users

    def test_cqrs_type_safety(self):
        """Test CQRS type safety."""
        class TestCommand(ICommand[int]):
            value: int

        class TestQuery(IQuery[bool]):
            flag: bool

        # These should work without type errors
        command = TestCommand(value=42)
        query = TestQuery(flag=True)

        assert command.value == 42
        assert query.flag is True

    def test_cqrs_validation(self):
        """Test CQRS validation."""
        class TestCommand(ICommand[str]):
            name: str
            age: int

        # Valid command
        command = TestCommand(name="John", age=30)
        assert command.name == "John"
        assert command.age == 30

        # Invalid command should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            TestCommand(name="John", age="invalid")

    def test_cqrs_serialization(self):
        """Test CQRS serialization."""
        class TestCommand(ICommand[str]):
            name: str
            data: dict

        command = TestCommand(name="test", data={"key": "value"})
        
        # Test model_dump
        command_dict = command.model_dump()
        assert command_dict["name"] == "test"
        assert command_dict["data"] == {"key": "value"}

        # Test model_dump_json
        command_json = command.model_dump_json()
        assert "test" in command_json
        assert "key" in command_json

    def test_cqrs_copy(self):
        """Test CQRS copy functionality."""
        class TestCommand(ICommand[str]):
            name: str
            data: dict

        original = TestCommand(name="original", data={"key": "value"})
        copied = original.model_copy(update={"name": "copied"})
        
        assert copied.name == "copied"
        assert copied.data == {"key": "value"}
        assert original.name == "original"  # Original unchanged


class TestCQRSComplexTypes:
    """Test CQRS with complex types."""

    def test_cqrs_with_nested_models(self):
        """Test CQRS with nested Pydantic models."""
        class Address(BaseModel):
            street: str
            city: str
            country: str

        class UserCommand(ICommand[str]):
            name: str
            address: Address

        command = UserCommand(
            name="John Doe",
            address=Address(street="123 Main St", city="New York", country="USA")
        )

        assert command.name == "John Doe"
        assert command.address.street == "123 Main St"
        assert command.address.city == "New York"
        assert command.address.country == "USA"

    def test_cqrs_with_optional_fields(self):
        """Test CQRS with optional fields."""
        from typing import Optional

        class OptionalCommand(ICommand[str]):
            required_field: str
            optional_field: Optional[str] = None

        # With optional field
        command1 = OptionalCommand(required_field="required")
        assert command1.required_field == "required"
        assert command1.optional_field is None

        # Without optional field
        command2 = OptionalCommand(required_field="required", optional_field="optional")
        assert command2.required_field == "required"
        assert command2.optional_field == "optional"

    def test_cqrs_with_lists(self):
        """Test CQRS with list fields."""
        class ListCommand(ICommand[str]):
            items: list[str]
            numbers: list[int]

        command = ListCommand(items=["a", "b", "c"], numbers=[1, 2, 3])
        
        assert command.items == ["a", "b", "c"]
        assert command.numbers == [1, 2, 3]

    def test_cqrs_with_enums(self):
        """Test CQRS with enum fields."""
        from enum import Enum

        class Status(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class StatusCommand(ICommand[str]):
            status: Status

        command = StatusCommand(status=Status.ACTIVE)
        assert command.status == Status.ACTIVE
