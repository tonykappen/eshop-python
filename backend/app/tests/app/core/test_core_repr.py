"""Tests for the REPR module."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from app.core.contracts.cqrs import ICommand, IQuery
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.mediator import IMediator
from app.core.repr.base import (BaseRequest, BaseResponse, CommandEndpoint,
                                CQRSEndpoint, CQRSEndpointFactory,
                                CQRSErrorHandler, DataResponse, Endpoint,
                                ErrorResponse, IRequestMapper, IResultMapper,
                                PaginatedRequest, PaginatedResponse,
                                PaginatedResultToResponseMapper, QueryEndpoint,
                                RequestToCommandMapper, RequestToQueryMapper,
                                ResultToBaseResponseMapper,
                                ResultToDataResponseMapper)
from fastapi import Request
from pydantic import BaseModel


@pytest.mark.no_collect
class TestRequest(BaseRequest):
    """Test request class."""

    name: str
    value: int


@pytest.mark.no_collect
class TestCommand(ICommand[Any]):
    """Test command class."""

    name: str
    value: int


@pytest.mark.no_collect
class TestQuery(IQuery[Any]):
    """Test query class."""

    name: str
    value: int


@pytest.mark.no_collect
class TestResult(BaseModel):
    """Test result class."""

    id: UUID
    name: str
    value: int


@pytest.mark.no_collect
class TestPaginatedResult(BaseModel):
    """Test paginated result class."""

    items: list[TestResult]
    total: int
    page: int
    size: int
    pages: int


class TestBaseRequest:
    """Test BaseRequest class."""

    def test_base_request_creation(self) -> None:
        """Test BaseRequest creation."""
        request = TestRequest(name="test", value=42)

        assert request.name == "test"
        assert request.value == 42
        assert isinstance(request, BaseRequest)


class TestBaseResponse:
    """Test BaseResponse class."""

    def test_base_response_default_values(self) -> None:
        """Test BaseResponse with default values."""
        response = BaseResponse()

        assert response.success is True
        assert response.message == ""
        assert isinstance(response.timestamp, str)
        assert len(response.timestamp) > 0

    def test_base_response_custom_values(self) -> None:
        """Test BaseResponse with custom values."""
        custom_timestamp = datetime.now(UTC).isoformat()
        response = BaseResponse(
            success=False, message="Custom message", timestamp=custom_timestamp
        )

        assert response.success is False
        assert response.message == "Custom message"
        assert response.timestamp == custom_timestamp

    def test_base_response_serialization(self) -> None:
        """Test BaseResponse serialization."""
        response = BaseResponse(success=True, message="Test message")

        response_dict = response.model_dump()
        assert response_dict["success"] is True
        assert response_dict["message"] == "Test message"
        assert "timestamp" in response_dict


class TestErrorResponse:
    """Test ErrorResponse class."""

    def test_error_response_default_values(self) -> None:
        """Test ErrorResponse with default values."""
        response = ErrorResponse()

        assert response.success is False
        assert response.message == ""
        assert response.error_code == ""
        assert response.details == {}

    def test_error_response_custom_values(self) -> None:
        """Test ErrorResponse with custom values."""
        response = ErrorResponse(
            message="Error occurred", error_code="TEST_ERROR", details={"key": "value"}
        )

        assert response.success is False
        assert response.message == "Error occurred"
        assert response.error_code == "TEST_ERROR"
        assert response.details == {"key": "value"}

    def test_error_response_inheritance(self) -> None:
        """Test ErrorResponse inheritance from BaseResponse."""
        response = ErrorResponse(message="Test")

        assert isinstance(response, BaseResponse)
        assert isinstance(response, ErrorResponse)


class TestDataResponse:
    """Test DataResponse class."""

    def test_data_response_creation(self) -> None:
        """Test DataResponse creation."""
        result = TestResult(id=uuid4(), name="test", value=42)
        response = DataResponse[TestResult](
            data=result, message="Data retrieved successfully"
        )

        assert response.success is True
        assert response.message == "Data retrieved successfully"
        assert response.data == result
        assert isinstance(response.data, TestResult)

    def test_data_response_serialization(self) -> None:
        """Test DataResponse serialization."""
        result = TestResult(id=uuid4(), name="test", value=42)
        response = DataResponse[TestResult](data=result)

        response_dict = response.model_dump()
        assert response_dict["success"] is True
        assert "data" in response_dict
        assert response_dict["data"]["name"] == "test"


class TestPaginatedRequest:
    """Test PaginatedRequest class."""

    def test_paginated_request_default_values(self) -> None:
        """Test PaginatedRequest with default values."""
        request = PaginatedRequest()

        assert request.page == 1
        assert request.page_size == 10
        assert request.offset == 0

    def test_paginated_request_custom_values(self) -> None:
        """Test PaginatedRequest with custom values."""
        request = PaginatedRequest(page=3, page_size=25)

        assert request.page == 3
        assert request.page_size == 25
        assert request.offset == 50

    def test_paginated_request_offset_calculation(self) -> None:
        """Test offset calculation."""
        request = PaginatedRequest(page=5, page_size=20)

        assert request.offset == 80

    def test_paginated_request_validation(self) -> None:
        """Test PaginatedRequest validation."""
        # Test valid values
        request = PaginatedRequest(page=1, page_size=50)
        assert request.page == 1
        assert request.page_size == 50

        # Test minimum values
        request = PaginatedRequest(page=1, page_size=1)
        assert request.page == 1
        assert request.page_size == 1

        # Test maximum page_size
        request = PaginatedRequest(page=1, page_size=100)
        assert request.page_size == 100


class TestPaginatedResponse:
    """Test PaginatedResponse class."""

    def test_paginated_response_creation(self) -> None:
        """Test PaginatedResponse creation."""
        results = [
            TestResult(id=uuid4(), name="item1", value=1),
            TestResult(id=uuid4(), name="item2", value=2),
        ]

        response = PaginatedResponse[TestResult](
            items=results,
            total=100,
            page=2,
            size=10,
            pages=10,
            message="Paginated data",
        )

        assert response.items == results
        assert response.total == 100
        assert response.page == 2
        assert response.size == 10
        assert response.pages == 10
        assert response.message == "Paginated data"

    def test_paginated_response_properties(self) -> None:
        """Test PaginatedResponse properties."""
        results = [TestResult(id=uuid4(), name="item", value=1)]

        # Test has_next
        response = PaginatedResponse[TestResult](
            items=results, total=30, page=1, size=10, pages=3
        )
        assert response.has_next is True

        # Test has_previous
        response = PaginatedResponse[TestResult](
            items=results, total=30, page=2, size=10, pages=3
        )
        assert response.has_previous is True

        # Test no next page
        response = PaginatedResponse[TestResult](
            items=results, total=30, page=3, size=10, pages=3
        )
        assert response.has_next is False

        # Test no previous page
        response = PaginatedResponse[TestResult](
            items=results, total=30, page=1, size=10, pages=3
        )
        assert response.has_previous is False


class TestIRequestMapper:
    """Test IRequestMapper interface."""

    def test_request_mapper_interface(self) -> None:
        """Test IRequestMapper interface definition."""
        # This test ensures the interface is properly defined
        assert hasattr(IRequestMapper, "map_to_command_or_query")

        # Test that it's an abstract method
        with pytest.raises(TypeError):
            IRequestMapper()  # type: ignore


class TestIResultMapper:
    """Test IResultMapper interface."""

    def test_result_mapper_interface(self) -> None:
        """Test IResultMapper interface definition."""
        # This test ensures the interface is properly defined
        assert hasattr(IResultMapper, "map_to_response")

        # Test that it's an abstract method
        with pytest.raises(TypeError):
            IResultMapper()  # type: ignore


class TestRequestToCommandMapper:
    """Test RequestToCommandMapper class."""

    def test_request_to_command_mapper_init(self) -> None:
        """Test RequestToCommandMapper initialization."""
        mapper = RequestToCommandMapper[TestRequest, TestCommand](TestCommand)

        assert mapper.command_factory == TestCommand

    @pytest.mark.asyncio
    async def test_map_to_command_or_query(self) -> None:
        """Test mapping request to command."""
        mapper = RequestToCommandMapper[TestRequest, TestCommand](TestCommand)
        request = TestRequest(name="test", value=42)
        mock_http_request = MagicMock(spec=Request)

        command = await mapper.map_to_command_or_query(request, mock_http_request)

        assert isinstance(command, TestCommand)
        assert command.name == "test"
        assert command.value == 42

    @pytest.mark.asyncio
    async def test_map_to_command_or_query_with_context(self) -> None:
        """Test mapping request to command with context."""

        class ContextMapper(RequestToCommandMapper[TestRequest, TestCommand]):
            async def _add_request_context(
                self, data: dict[str, Any], _request: Request
            ) -> dict[str, Any]:
                data["context"] = "added"
                return data

        mapper = ContextMapper(TestCommand)
        request = TestRequest(name="test", value=42)
        mock_http_request = MagicMock(spec=Request)

        command = await mapper.map_to_command_or_query(request, mock_http_request)

        assert isinstance(command, TestCommand)
        assert command.name == "test"
        assert command.value == 42


class TestRequestToQueryMapper:
    """Test RequestToQueryMapper class."""

    def test_request_to_query_mapper_init(self) -> None:
        """Test RequestToQueryMapper initialization."""
        mapper = RequestToQueryMapper[TestRequest, TestQuery](TestQuery)

        assert mapper.query_factory == TestQuery

    @pytest.mark.asyncio
    async def test_map_to_command_or_query(self) -> None:
        """Test mapping request to query."""
        mapper = RequestToQueryMapper[TestRequest, TestQuery](TestQuery)
        request = TestRequest(name="test", value=42)
        mock_http_request = MagicMock(spec=Request)

        query = await mapper.map_to_command_or_query(request, mock_http_request)

        assert isinstance(query, TestQuery)
        assert query.name == "test"
        assert query.value == 42


class TestResultToDataResponseMapper:
    """Test ResultToDataResponseMapper class."""

    @pytest.mark.asyncio
    async def test_map_to_response(self) -> None:
        """Test mapping result to data response."""
        mapper = ResultToDataResponseMapper[TestResult]()
        result = TestResult(id=uuid4(), name="test", value=42)
        mock_request = MagicMock(spec=Request)

        response = await mapper.map_to_response(result, mock_request)

        assert isinstance(response, DataResponse)
        assert response.data == result
        assert response.message == "Operation completed successfully"
        assert response.success is True


class TestResultToBaseResponseMapper:
    """Test ResultToBaseResponseMapper class."""

    @pytest.mark.asyncio
    async def test_map_to_response(self) -> None:
        """Test mapping result to base response."""
        mapper = ResultToBaseResponseMapper()
        result = "success"
        mock_request = MagicMock(spec=Request)

        response = await mapper.map_to_response(result, mock_request)

        assert isinstance(response, BaseResponse)
        assert response.message == "Operation completed successfully"
        assert response.success is True


class TestPaginatedResultToResponseMapper:
    """Test PaginatedResultToResponseMapper class."""

    @pytest.mark.asyncio
    async def test_map_to_response(self) -> None:
        """Test mapping paginated result to response."""
        mapper = PaginatedResultToResponseMapper[TestResult]()

        results = [
            TestResult(id=uuid4(), name="item1", value=1),
            TestResult(id=uuid4(), name="item2", value=2),
        ]

        result = TestPaginatedResult(
            items=results, total=100, page=2, size=10, pages=10
        )

        mock_request = MagicMock(spec=Request)

        response = await mapper.map_to_response(result, mock_request)

        assert isinstance(response, PaginatedResponse)
        assert response.data == results
        assert response.total_count == 100
        assert response.page == 2
        assert response.page_size == 10
        assert response.total_pages == 10
        assert response.message == "Paginated data retrieved successfully"


class TestEndpoint:
    """Test Endpoint base class."""

    def test_endpoint_interface(self) -> None:
        """Test Endpoint interface definition."""
        # This test ensures the interface is properly defined
        assert hasattr(Endpoint, "handle")
        assert hasattr(Endpoint, "check_disconnection")
        assert hasattr(Endpoint, "execute")

        # Test that it's an abstract method
        with pytest.raises(TypeError):
            Endpoint()  # type: ignore

    @pytest.mark.asyncio
    async def test_check_disconnection(self) -> None:
        """Test disconnection check."""

        class TestEndpointImpl(Endpoint[TestRequest, BaseResponse]):
            async def handle(
                self, _request: Request, _data: TestRequest
            ) -> BaseResponse:
                return BaseResponse()

        endpoint = TestEndpointImpl()
        mock_request = AsyncMock(spec=Request)
        mock_request.is_disconnected.return_value = False

        result = await endpoint.check_disconnection(mock_request)

        assert result is False
        mock_request.is_disconnected.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_success(self) -> None:
        """Test successful execution."""

        class TestEndpointImpl(Endpoint[TestRequest, BaseResponse]):
            async def handle(
                self, _request: Request, _data: TestRequest
            ) -> BaseResponse:
                return BaseResponse(message="Success")

        endpoint = TestEndpointImpl()
        mock_request = AsyncMock(spec=Request)
        mock_request.is_disconnected.return_value = False
        data = TestRequest(name="test", value=42)

        response = await endpoint.execute(mock_request, data)

        assert isinstance(response, BaseResponse)
        assert response.message == "Success"

    @pytest.mark.asyncio
    async def test_execute_disconnected(self) -> None:
        """Test execution with disconnected client."""

        class TestEndpointImpl(Endpoint[TestRequest, BaseResponse]):
            async def handle(
                self, _request: Request, _data: TestRequest
            ) -> BaseResponse:
                return BaseResponse()

        endpoint = TestEndpointImpl()
        mock_request = AsyncMock(spec=Request)
        mock_request.is_disconnected.return_value = True
        data = TestRequest(name="test", value=42)

        with pytest.raises(ConnectionError, match="Client disconnected"):
            await endpoint.execute(mock_request, data)


class TestCQRSEndpoint:
    """Test CQRSEndpoint class."""

    def test_cqrs_endpoint_init(self) -> None:
        """Test CQRSEndpoint initialization."""
        mock_request_mapper = MagicMock(spec=IRequestMapper)
        mock_result_mapper = MagicMock(spec=IResultMapper)
        mock_mediator = MagicMock(spec=IMediator)

        endpoint = CQRSEndpoint[TestRequest, BaseResponse](
            mock_request_mapper, mock_result_mapper, mock_mediator
        )

        assert endpoint.request_mapper == mock_request_mapper
        assert endpoint.result_mapper == mock_result_mapper
        assert endpoint.mediator == mock_mediator

    @pytest.mark.asyncio
    async def test_handle_success(self) -> None:
        """Test successful CQRS endpoint handling."""
        mock_request_mapper = AsyncMock(spec=IRequestMapper)
        mock_result_mapper = AsyncMock(spec=IResultMapper)
        mock_mediator = AsyncMock(spec=IMediator)

        # Setup mocks
        command = TestCommand(name="test", value=42)
        result = TestResult(id=uuid4(), name="result", value=100)
        response = BaseResponse(message="Success")

        mock_request_mapper.map_to_command_or_query.return_value = command
        mock_mediator.send.return_value = result
        mock_result_mapper.map_to_response.return_value = response

        endpoint = CQRSEndpoint[TestRequest, BaseResponse](
            mock_request_mapper, mock_result_mapper, mock_mediator
        )

        mock_request = MagicMock(spec=Request)
        data = TestRequest(name="test", value=42)

        result_response = await endpoint.handle(mock_request, data)

        # Verify the flow
        mock_request_mapper.map_to_command_or_query.assert_called_once_with(
            data, mock_request
        )
        mock_mediator.send.assert_called_once()
        mock_result_mapper.map_to_response.assert_called_once_with(result, mock_request)
        assert result_response == response

    @pytest.mark.asyncio
    async def test_handle_with_cancellation_token(self) -> None:
        """Test CQRS endpoint handling with cancellation token."""
        mock_request_mapper = AsyncMock(spec=IRequestMapper)
        mock_result_mapper = AsyncMock(spec=IResultMapper)
        mock_mediator = AsyncMock(spec=IMediator)

        command = TestCommand(name="test", value=42)
        result = TestResult(id=uuid4(), name="result", value=100)
        response = BaseResponse(message="Success")

        mock_request_mapper.map_to_command_or_query.return_value = command
        mock_mediator.send.return_value = result
        mock_result_mapper.map_to_response.return_value = response

        endpoint = CQRSEndpoint[TestRequest, BaseResponse](
            mock_request_mapper, mock_result_mapper, mock_mediator
        )

        mock_request = MagicMock(spec=Request)
        data = TestRequest(name="test", value=42)

        await endpoint.handle(mock_request, data)

        # Verify cancellation token was used
        call_args = mock_mediator.send.call_args
        assert len(call_args[0]) == 2  # command and cancellation_token
        assert isinstance(call_args[0][1], CancellationToken)


class TestCommandEndpoint:
    """Test CommandEndpoint class."""

    def test_command_endpoint_init(self) -> None:
        """Test CommandEndpoint initialization."""
        mock_result_mapper = MagicMock(spec=IResultMapper)
        mock_mediator = MagicMock(spec=IMediator)

        endpoint = CommandEndpoint[TestRequest, BaseResponse](
            TestCommand, mock_result_mapper, mock_mediator
        )

        assert isinstance(endpoint.request_mapper, RequestToCommandMapper)
        assert endpoint.request_mapper.command_factory == TestCommand
        assert endpoint.result_mapper == mock_result_mapper
        assert endpoint.mediator == mock_mediator


class TestQueryEndpoint:
    """Test QueryEndpoint class."""

    def test_query_endpoint_init(self) -> None:
        """Test QueryEndpoint initialization."""
        mock_result_mapper = MagicMock(spec=IResultMapper)
        mock_mediator = MagicMock(spec=IMediator)

        endpoint = QueryEndpoint[TestRequest, BaseResponse](
            TestQuery, mock_result_mapper, mock_mediator
        )

        assert isinstance(endpoint.request_mapper, RequestToQueryMapper)
        assert endpoint.request_mapper.query_factory == TestQuery
        assert endpoint.result_mapper == mock_result_mapper
        assert endpoint.mediator == mock_mediator


class TestCQRSErrorHandler:
    """Test CQRSErrorHandler class."""

    @pytest.mark.asyncio
    async def test_handle_validation_error(self) -> None:
        """Test handling ValueError."""
        mock_request = MagicMock(spec=Request)
        error = ValueError("Invalid data")

        response = await CQRSErrorHandler.handle_error(error, mock_request)

        assert isinstance(response, ErrorResponse)
        assert response.success is False
        assert response.message == "Invalid request data"
        assert response.error_code == "VALIDATION_ERROR"
        assert "Invalid data" in response.details["error"]

    @pytest.mark.asyncio
    async def test_handle_permission_error(self) -> None:
        """Test handling PermissionError."""
        mock_request = MagicMock(spec=Request)
        error = PermissionError("Access denied")

        response = await CQRSErrorHandler.handle_error(error, mock_request)

        assert isinstance(response, ErrorResponse)
        assert response.success is False
        assert response.message == "Access denied"
        assert response.error_code == "AUTHORIZATION_ERROR"

    @pytest.mark.asyncio
    async def test_handle_file_not_found_error(self) -> None:
        """Test handling FileNotFoundError."""
        mock_request = MagicMock(spec=Request)
        error = FileNotFoundError("File not found")

        response = await CQRSErrorHandler.handle_error(error, mock_request)

        assert isinstance(response, ErrorResponse)
        assert response.success is False
        assert response.message == "Resource not found"
        assert response.error_code == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_handle_generic_error(self) -> None:
        """Test handling generic exception."""
        mock_request = MagicMock(spec=Request)
        error = RuntimeError("Something went wrong")

        response = await CQRSErrorHandler.handle_error(error, mock_request)

        assert isinstance(response, ErrorResponse)
        assert response.success is False
        assert response.message == "An unexpected error occurred"
        assert response.error_code == "INTERNAL_ERROR"


class TestCQRSEndpointFactory:
    """Test CQRSEndpointFactory class."""

    def test_cqrs_endpoint_factory_init(self) -> None:
        """Test CQRSEndpointFactory initialization."""
        mock_mediator = MagicMock(spec=IMediator)

        factory = CQRSEndpointFactory(mock_mediator)

        assert factory.mediator == mock_mediator

    def test_create_command_endpoint_default_mapper(self) -> None:
        """Test creating command endpoint with default mapper."""
        mock_mediator = MagicMock(spec=IMediator)
        factory = CQRSEndpointFactory(mock_mediator)

        endpoint = factory.create_command_endpoint(TestCommand)

        assert isinstance(endpoint, CommandEndpoint)
        assert isinstance(endpoint.request_mapper, RequestToCommandMapper)
        assert endpoint.request_mapper.command_factory == TestCommand
        assert isinstance(endpoint.result_mapper, ResultToDataResponseMapper)
        assert endpoint.mediator == mock_mediator

    def test_create_command_endpoint_custom_mapper(self) -> None:
        """Test creating command endpoint with custom mapper."""
        mock_mediator = MagicMock(spec=IMediator)
        mock_result_mapper = MagicMock(spec=IResultMapper)
        factory = CQRSEndpointFactory(mock_mediator)

        endpoint = factory.create_command_endpoint(TestCommand, mock_result_mapper)

        assert isinstance(endpoint, CommandEndpoint)
        assert endpoint.result_mapper == mock_result_mapper

    def test_create_query_endpoint_default_mapper(self) -> None:
        """Test creating query endpoint with default mapper."""
        mock_mediator = MagicMock(spec=IMediator)
        factory = CQRSEndpointFactory(mock_mediator)

        endpoint = factory.create_query_endpoint(TestQuery)

        assert isinstance(endpoint, QueryEndpoint)
        assert isinstance(endpoint.request_mapper, RequestToQueryMapper)
        assert endpoint.request_mapper.query_factory == TestQuery
        assert isinstance(endpoint.result_mapper, ResultToDataResponseMapper)
        assert endpoint.mediator == mock_mediator

    def test_create_query_endpoint_custom_mapper(self) -> None:
        """Test creating query endpoint with custom mapper."""
        mock_mediator = MagicMock(spec=IMediator)
        mock_result_mapper = MagicMock(spec=IResultMapper)
        factory = CQRSEndpointFactory(mock_mediator)

        endpoint = factory.create_query_endpoint(TestQuery, mock_result_mapper)

        assert isinstance(endpoint, QueryEndpoint)
        assert endpoint.result_mapper == mock_result_mapper


class TestREPRIntegration:
    """Integration tests for REPR functionality."""

    @pytest.mark.asyncio
    async def test_complete_cqrs_flow(self) -> None:
        """Test complete CQRS flow through REPR pattern."""
        # Setup
        mock_mediator = AsyncMock(spec=IMediator)
        factory = CQRSEndpointFactory(mock_mediator)

        # Create command endpoint
        command_endpoint = factory.create_command_endpoint(TestCommand)

        # Setup mediator response
        result = "success"
        mock_mediator.send.return_value = result

        # Execute
        mock_request = MagicMock(spec=Request)
        data = TestRequest(name="test", value=42)

        response = await command_endpoint.handle(mock_request, data)

        # Verify
        assert isinstance(response, BaseResponse)
        assert response.success is True
        assert response.message == "Operation completed successfully"

        # Verify mediator was called with command
        mock_mediator.send.assert_called_once()
        call_args = mock_mediator.send.call_args
        command = call_args[0][0]
        assert isinstance(command, TestCommand)
        assert command.name == "test"
        assert command.value == 42

    @pytest.mark.asyncio
    async def test_complete_query_flow(self) -> None:
        """Test complete query flow through REPR pattern."""
        # Setup
        mock_mediator = AsyncMock(spec=IMediator)
        factory = CQRSEndpointFactory(mock_mediator)

        # Create query endpoint
        query_endpoint = factory.create_query_endpoint(TestQuery)

        # Setup mediator response
        result = TestResult(id=uuid4(), name="result", value=100)
        mock_mediator.send.return_value = result

        # Execute
        mock_request = MagicMock(spec=Request)
        data = TestRequest(name="test", value=42)

        response = await query_endpoint.handle(mock_request, data)

        # Verify
        assert isinstance(response, DataResponse)
        assert response.data == result
        assert response.success is True
        assert response.message == "Operation completed successfully"

        # Verify mediator was called with query
        mock_mediator.send.assert_called_once()
        call_args = mock_mediator.send.call_args
        query = call_args[0][0]
        assert isinstance(query, TestQuery)
        assert query.name == "test"
        assert query.value == 42

    def test_pagination_workflow(self) -> None:
        """Test pagination workflow."""
        # Create paginated request
        request = PaginatedRequest(page=2, page_size=10)
        assert request.offset == 10

        # Create paginated response
        results = [TestResult(id=uuid4(), name="item", value=1)]
        response = PaginatedResponse[TestResult](
            items=results, total=25, page=2, size=10, pages=3
        )

        assert response.has_next is True
        assert response.has_previous is True
        assert response.pages == 3

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self) -> None:
        """Test error handling workflow."""
        mock_request = MagicMock(spec=Request)

        # Test different error types
        errors = [
            (ValueError("Invalid input"), "VALIDATION_ERROR"),
            (PermissionError("No access"), "AUTHORIZATION_ERROR"),
            (FileNotFoundError("Not found"), "NOT_FOUND"),
            (RuntimeError("Unknown error"), "INTERNAL_ERROR"),
        ]

        for error, expected_code in errors:
            response = await CQRSErrorHandler.handle_error(error, mock_request)

            assert isinstance(response, ErrorResponse)
            assert response.success is False
            assert response.error_code == expected_code
            assert str(error) in response.details["error"]
