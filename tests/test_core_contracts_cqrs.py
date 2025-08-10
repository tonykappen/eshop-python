"""Comprehensive tests for the CQRS contracts."""

from enum import Enum

import pytest
from pydantic import BaseModel, ValidationError

from eshop.core.contracts.cqrs import (
    ICommand,
    ICommandHandler,
    ICommandHandlerNoResponse,
    ICommandNoResponse,
    IQuery,
    IQueryHandler,
)


class TestICommand:
    """Test ICommand interface behavior."""

    def test_icommand_inheritance_and_configuration(self):
        """Test that ICommand inherits from BaseModel with correct configuration."""
        assert issubclass(ICommand, BaseModel)
        assert hasattr(ICommand, "Config")
        assert hasattr(ICommand.Config, "arbitrary_types_allowed")
        assert ICommand.Config.arbitrary_types_allowed is True

    def test_icommand_generic_type_behavior(self):
        """Test ICommand generic type parameter behavior."""
        class TestCommand(ICommand[str]):
            name: str
            value: int

        command = TestCommand(name="test", value=42)
        assert command.name == "test"
        assert command.value == 42
        assert isinstance(command, ICommand)

        # Test that it can be serialized
        command_dict = command.model_dump()
        assert command_dict["name"] == "test"
        assert command_dict["value"] == 42

    def test_icommand_validation_behavior(self):
        """Test ICommand validation behavior."""
        class TestCommand(ICommand[str]):
            name: str
            age: int

        # Valid command should work
        command = TestCommand(name="test", age=25)
        assert command.name == "test"
        assert command.age == 25

        # Invalid command should raise validation error
        with pytest.raises(ValidationError):
            TestCommand(name="test", age="invalid")

    def test_icommand_serialization_behavior(self):
        """Test ICommand serialization behavior."""
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
        assert '"name":"test"' in command_json
        assert '"key":"value"' in command_json


class TestICommandNoResponse:
    """Test ICommandNoResponse interface behavior."""

    def test_icommand_no_response_inheritance_chain(self):
        """Test that ICommandNoResponse inherits from ICommand."""
        assert issubclass(ICommandNoResponse, ICommand)

    def test_icommand_no_response_behavior(self):
        """Test ICommandNoResponse behavior."""
        class TestCommand(ICommandNoResponse):
            name: str
            action: str

        command = TestCommand(name="test", action="delete")
        assert command.name == "test"
        assert command.action == "delete"
        assert isinstance(command, ICommandNoResponse)
        assert isinstance(command, ICommand)

        # Test serialization
        command_dict = command.model_dump()
        assert command_dict["name"] == "test"
        assert command_dict["action"] == "delete"


class TestIQuery:
    """Test IQuery interface behavior."""

    def test_iquery_inheritance_and_configuration(self):
        """Test that IQuery inherits from BaseModel with correct configuration."""
        assert issubclass(IQuery, BaseModel)
        assert hasattr(IQuery, "Config")
        assert hasattr(IQuery.Config, "arbitrary_types_allowed")
        assert IQuery.Config.arbitrary_types_allowed is True

    def test_iquery_generic_type_behavior(self):
        """Test IQuery generic type parameter behavior."""
        class TestQuery(IQuery[dict]):
            id: str
            include_details: bool

        query = TestQuery(id="123", include_details=True)
        assert query.id == "123"
        assert query.include_details is True
        assert isinstance(query, IQuery)

        # Test serialization
        query_dict = query.model_dump()
        assert query_dict["id"] == "123"
        assert query_dict["include_details"] is True

    def test_iquery_validation_behavior(self):
        """Test IQuery validation behavior."""
        class TestQuery(IQuery[list]):
            limit: int
            offset: int

        # Valid query should work
        query = TestQuery(limit=10, offset=0)
        assert query.limit == 10
        assert query.offset == 0

        # Invalid query should raise validation error
        with pytest.raises(ValidationError):
            TestQuery(limit="invalid", offset=0)


class TestICommandHandler:
    """Test ICommandHandler interface behavior."""

    def test_icommand_handler_abstract_method_enforcement(self):
        """Test that ICommandHandler enforces abstract handle method."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            ICommandHandler()

    def test_icommand_handler_implementation_behavior(self):
        """Test ICommandHandler implementation behavior."""
        class TestCommand(ICommand[str]):
            name: str
            value: int

        class TestCommandHandler(ICommandHandler[TestCommand, str]):
            async def handle(self, command: TestCommand) -> str:
                return f"Handled: {command.name} with value {command.value}"

        handler = TestCommandHandler()
        assert isinstance(handler, ICommandHandler)

    @pytest.mark.asyncio
    async def test_icommand_handler_usage_behavior(self):
        """Test ICommandHandler usage behavior."""
        class TestCommand(ICommand[str]):
            name: str
            operation: str

        class TestCommandHandler(ICommandHandler[TestCommand, str]):
            async def handle(self, command: TestCommand) -> str:
                if command.operation == "create":
                    return f"Created: {command.name}"
                elif command.operation == "update":
                    return f"Updated: {command.name}"
                else:
                    return f"Unknown operation: {command.operation}"

        handler = TestCommandHandler()
        command = TestCommand(name="test", operation="create")
        result = await handler.handle(command)
        assert result == "Created: test"

        # Test different operation
        command.operation = "update"
        result = await handler.handle(command)
        assert result == "Updated: test"


class TestICommandHandlerNoResponse:
    """Test ICommandHandlerNoResponse interface behavior."""

    def test_icommand_handler_no_response_abstract_method_enforcement(self):
        """Test that ICommandHandlerNoResponse enforces abstract handle method."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            ICommandHandlerNoResponse()

    def test_icommand_handler_no_response_implementation_behavior(self):
        """Test ICommandHandlerNoResponse implementation behavior."""
        class TestCommand(ICommandNoResponse):
            name: str
            action: str

        class TestCommandHandler(ICommandHandlerNoResponse[TestCommand]):
            def __init__(self):
                self.processed_commands = []

            async def handle(self, command: TestCommand) -> None:
                self.processed_commands.append(f"{command.action}: {command.name}")

        handler = TestCommandHandler()
        assert isinstance(handler, ICommandHandlerNoResponse)

    @pytest.mark.asyncio
    async def test_icommand_handler_no_response_usage_behavior(self):
        """Test ICommandHandlerNoResponse usage behavior."""
        class TestCommand(ICommandNoResponse):
            name: str
            action: str

        class TestCommandHandler(ICommandHandlerNoResponse[TestCommand]):
            def __init__(self):
                self.processed_commands = []

            async def handle(self, command: TestCommand) -> None:
                self.processed_commands.append(f"{command.action}: {command.name}")

        handler = TestCommandHandler()
        command = TestCommand(name="test", action="delete")

        # Should return None
        result = await handler.handle(command)
        assert result is None

        # Should have processed the command
        assert len(handler.processed_commands) == 1
        assert handler.processed_commands[0] == "delete: test"


class TestIQueryHandler:
    """Test IQueryHandler interface behavior."""

    def test_iquery_handler_abstract_method_enforcement(self):
        """Test that IQueryHandler enforces abstract handle method."""
        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            IQueryHandler()

    def test_iquery_handler_implementation_behavior(self):
        """Test IQueryHandler implementation behavior."""
        class TestQuery(IQuery[dict]):
            id: str
            include_details: bool

        class TestQueryHandler(IQueryHandler[TestQuery, dict]):
            async def handle(self, query: TestQuery) -> dict:
                return {
                    "id": query.id,
                    "details": "some details" if query.include_details else None
                }

        handler = TestQueryHandler()
        assert isinstance(handler, IQueryHandler)

    @pytest.mark.asyncio
    async def test_iquery_handler_usage_behavior(self):
        """Test IQueryHandler usage behavior."""
        class TestQuery(IQuery[dict]):
            id: str
            include_details: bool

        class TestQueryHandler(IQueryHandler[TestQuery, dict]):
            async def handle(self, query: TestQuery) -> dict:
                base_data = {"id": query.id, "name": "Test User"}
                if query.include_details:
                    base_data.update({
                        "email": "test@example.com",
                        "created_at": "2023-01-01"
                    })
                return base_data

        handler = TestQueryHandler()
        query = TestQuery(id="123", include_details=True)
        result = await handler.handle(query)

        assert result["id"] == "123"
        assert result["name"] == "Test User"
        assert result["email"] == "test@example.com"
        assert result["created_at"] == "2023-01-01"

        # Test without details
        query.include_details = False
        result = await handler.handle(query)
        assert result["id"] == "123"
        assert result["name"] == "Test User"
        assert "email" not in result


class TestCQRSIntegration:
    """Test CQRS integration scenarios."""

    @pytest.mark.asyncio
    async def test_command_handler_integration_behavior(self):
        """Test command handler integration behavior."""
        class CreateUserCommand(ICommand[str]):
            name: str
            email: str
            age: int

        class CreateUserHandler(ICommandHandler[CreateUserCommand, str]):
            async def handle(self, command: CreateUserCommand) -> str:
                # Simulate user creation logic
                if command.age < 18:
                    raise ValueError("User must be 18 or older")

                user_id = f"user_{len(command.name)}_{command.age}"
                return f"Created user {user_id} with email {command.email}"

        handler = CreateUserHandler()
        command = CreateUserCommand(name="John Doe", email="john@example.com", age=25)
        result = await handler.handle(command)

        assert "Created user user_8_25" in result
        assert "john@example.com" in result

        # Test validation in handler
        command.age = 16
        with pytest.raises(ValueError, match="User must be 18 or older"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_query_handler_integration_behavior(self):
        """Test query handler integration behavior."""
        class GetUserQuery(IQuery[dict]):
            user_id: str
            include_profile: bool

        class GetUserHandler(IQueryHandler[GetUserQuery, dict]):
            async def handle(self, query: GetUserQuery) -> dict:
                # Simulate user retrieval logic
                base_user = {
                    "id": query.user_id,
                    "name": "John Doe",
                    "email": "john@example.com"
                }

                if query.include_profile:
                    base_user.update({
                        "profile": {
                            "bio": "Software Developer",
                            "location": "New York",
                            "skills": ["Python", "FastAPI", "SQLAlchemy"]
                        }
                    })

                return base_user

        handler = GetUserHandler()
        query = GetUserQuery(user_id="123", include_profile=True)
        result = await handler.handle(query)

        assert result["id"] == "123"
        assert result["name"] == "John Doe"
        assert "profile" in result
        assert result["profile"]["skills"] == ["Python", "FastAPI", "SQLAlchemy"]

        # Test without profile
        query.include_profile = False
        result = await handler.handle(query)
        assert result["id"] == "123"
        assert "profile" not in result

    @pytest.mark.asyncio
    async def test_command_no_response_integration_behavior(self):
        """Test command no response integration behavior."""
        class DeleteUserCommand(ICommandNoResponse):
            user_id: str
            reason: str

        class DeleteUserHandler(ICommandHandlerNoResponse[DeleteUserCommand]):
            def __init__(self):
                self.deleted_users = []

            async def handle(self, command: DeleteUserCommand) -> None:
                # Simulate user deletion logic
                self.deleted_users.append({
                    "id": command.user_id,
                    "reason": command.reason,
                    "deleted_at": "2023-01-01T00:00:00Z"
                })

        handler = DeleteUserHandler()
        command = DeleteUserCommand(user_id="123", reason="Account closure")

        result = await handler.handle(command)
        assert result is None

        assert len(handler.deleted_users) == 1
        assert handler.deleted_users[0]["id"] == "123"
        assert handler.deleted_users[0]["reason"] == "Account closure"

    def test_cqrs_type_safety_behavior(self):
        """Test CQRS type safety behavior."""
        class TestCommand(ICommand[int]):
            value: int

        class TestQuery(IQuery[bool]):
            flag: bool

        # Test command type safety
        command = TestCommand(value=42)
        assert command.value == 42
        assert isinstance(command.value, int)

        # Test query type safety
        query = TestQuery(flag=True)
        assert query.flag is True
        assert isinstance(query.flag, bool)

    def test_cqrs_validation_behavior(self):
        """Test CQRS validation behavior."""
        class TestCommand(ICommand[str]):
            name: str
            age: int

        # Valid command
        command = TestCommand(name="test", age=25)
        assert command.name == "test"
        assert command.age == 25

        # Invalid command should raise validation error
        with pytest.raises(ValidationError):
            TestCommand(name="test", age="invalid")

    def test_cqrs_serialization_behavior(self):
        """Test CQRS serialization behavior."""
        class TestCommand(ICommand[str]):
            name: str
            data: dict

        command = TestCommand(name="test", data={"key": "value", "number": 42})

        # Test model_dump
        command_dict = command.model_dump()
        assert command_dict["name"] == "test"
        assert command_dict["data"] == {"key": "value", "number": 42}

        # Test model_dump_json
        command_json = command.model_dump_json()
        assert '"name":"test"' in command_json
        assert '"key":"value"' in command_json
        assert '"number":42' in command_json

    def test_cqrs_copy_behavior(self):
        """Test CQRS copy behavior."""
        class TestCommand(ICommand[str]):
            name: str
            data: dict

        command = TestCommand(name="test", data={"key": "value"})
        command_copy = command.model_copy()

        # Should be equal but different objects
        assert command == command_copy
        assert command is not command_copy

        # Modifying copy should not affect original
        command_copy.name = "modified"
        assert command.name == "test"
        assert command_copy.name == "modified"


class TestCQRSComplexTypes:
    """Test CQRS with complex types."""

    def test_cqrs_with_nested_models_behavior(self):
        """Test CQRS with nested models behavior."""
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

        # Test serialization with nested model
        command_dict = command.model_dump()
        assert command_dict["name"] == "John Doe"
        assert command_dict["address"]["street"] == "123 Main St"

    def test_cqrs_with_optional_fields_behavior(self):
        """Test CQRS with optional fields behavior."""
        class OptionalCommand(ICommand[str]):
            required_field: str
            optional_field: str | None = None

        # Test with optional field
        command = OptionalCommand(required_field="required")
        assert command.required_field == "required"
        assert command.optional_field is None

        # Test with optional field provided
        command = OptionalCommand(required_field="required", optional_field="optional")
        assert command.required_field == "required"
        assert command.optional_field == "optional"

    def test_cqrs_with_lists_behavior(self):
        """Test CQRS with lists behavior."""
        class ListCommand(ICommand[str]):
            items: list[str]
            numbers: list[int]

        command = ListCommand(items=["item1", "item2"], numbers=[1, 2, 3])

        assert command.items == ["item1", "item2"]
        assert command.numbers == [1, 2, 3]

        # Test serialization
        command_dict = command.model_dump()
        assert command_dict["items"] == ["item1", "item2"]
        assert command_dict["numbers"] == [1, 2, 3]

    def test_cqrs_with_enums_behavior(self):
        """Test CQRS with enums behavior."""
        class Status(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class StatusCommand(ICommand[str]):
            status: Status

        command = StatusCommand(status=Status.ACTIVE)
        assert command.status == Status.ACTIVE
        assert command.status.value == "active"

        # Test serialization
        command_dict = command.model_dump()
        assert command_dict["status"] == Status.ACTIVE
