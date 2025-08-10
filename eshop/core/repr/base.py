"""Enhanced REPR (Request-Endpoint-Response) pattern with CQRS integration.

This module implements the flow: Request -> Command/Query -> Result -> Response
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from fastapi import Request
from pydantic import BaseModel, Field

from eshop.core.contracts.cqrs import ICommand, IQuery
from eshop.core.mediator.cancellation import CancellationToken
from eshop.core.mediator.mediator import IMediator

# Type variables for REPR pattern
TRequest = TypeVar("TRequest", bound=BaseModel)
TResponse = TypeVar("TResponse", bound=BaseModel)
TCommand = TypeVar("TCommand", bound=ICommand[Any])
TQuery = TypeVar("TQuery", bound=IQuery[Any])
TResult = TypeVar("TResult")

# Union type for command or query
CommandOrQuery = ICommand[Any] | IQuery[Any]


class BaseRequest(BaseModel):
    """Base request class for REPR pattern."""

    class Config:
        arbitrary_types_allowed = True


class BaseResponse(BaseModel):
    """Base response class for REPR pattern."""

    success: bool = Field(
        default=True, description="Indicates if the operation was successful"
    )
    message: str = Field(default="", description="Optional message about the operation")
    timestamp: str = Field(
        default_factory=lambda: __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat(),
        description="Response timestamp",
    )

    class Config:
        arbitrary_types_allowed = True


class ErrorResponse(BaseResponse):
    """Response for error cases."""

    success: bool = Field(default=False)
    error_code: str = Field(default="", description="Error code for categorization")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error details"
    )


class DataResponse(BaseResponse, Generic[TResult]):
    """Response containing data payload."""

    data: TResult = Field(..., description="Response data payload")


class IRequestMapper(ABC):
    """Interface for mapping HTTP requests to commands/queries."""

    @abstractmethod
    async def map_to_command_or_query(self, request: Any, http_request: Request) -> Any:
        """Map HTTP request to command or query."""
        pass


class IResultMapper(Generic[TResult, TResponse], ABC):
    """Interface for mapping command/query results to HTTP responses."""

    @abstractmethod
    async def map_to_response(
        self, result: TResult, original_request: Request
    ) -> TResponse:
        """Map command/query result to HTTP response."""
        pass


class RequestToCommandMapper(IRequestMapper, Generic[TRequest, TCommand]):
    """Base implementation for mapping requests to commands."""

    def __init__(self, command_factory: type[TCommand]) -> None:
        self.command_factory = command_factory

    async def map_to_command_or_query(
        self, request: TRequest, http_request: Request
    ) -> TCommand:
        """Map request to command using factory."""
        # Extract command data from request
        command_data = request.model_dump()

        # Add request context if needed
        if hasattr(self, "_add_request_context"):
            command_data = await self._add_request_context(command_data, http_request)

        return self.command_factory(**command_data)


class RequestToQueryMapper(IRequestMapper, Generic[TRequest, TQuery]):
    """Base implementation for mapping requests to queries."""

    def __init__(self, query_factory: type[TQuery]) -> None:
        self.query_factory = query_factory

    async def map_to_command_or_query(
        self, request: TRequest, http_request: Request
    ) -> TQuery:
        """Map request to query using factory."""
        # Extract query data from request
        query_data = request.model_dump()

        # Add request context if needed
        if hasattr(self, "_add_request_context"):
            query_data = await self._add_request_context(query_data, http_request)

        return self.query_factory(**query_data)


class ResultToDataResponseMapper(
    IResultMapper[TResult, DataResponse[TResult]], Generic[TResult]
):
    """Maps command/query results to data responses."""

    async def map_to_response(
        self, result: TResult, original_request: Request  # noqa: ARG002
    ) -> DataResponse[TResult]:
        """Map result to data response."""
        return DataResponse[TResult](
            data=result, message="Operation completed successfully"
        )


class ResultToBaseResponseMapper(IResultMapper[Any, BaseResponse]):
    """Maps command results to base responses (for commands with no data)."""

    async def map_to_response(
        self, result: Any, original_request: Request  # noqa: ARG002
    ) -> BaseResponse:
        """Map result to base response."""
        return BaseResponse(success=True, message="Operation completed successfully")


class Endpoint(ABC, Generic[TRequest, TResponse]):
    """Base endpoint class following enhanced REPR pattern."""

    @abstractmethod
    async def handle(self, request: Request, data: TRequest) -> TResponse:
        """Handle the endpoint request."""
        pass

    async def check_disconnection(self, request: Request) -> bool:
        """Check if client has disconnected (collection token pattern)."""
        return await request.is_disconnected()

    async def execute(self, request: Request, data: TRequest) -> TResponse:
        """Execute the endpoint with disconnection check."""
        if await self.check_disconnection(request):
            raise ConnectionError("Client disconnected")

        return await self.handle(request, data)


class CQRSEndpoint(Endpoint[TRequest, TResponse], Generic[TRequest, TResponse]):
    """CQRS-enabled endpoint following request -> command/query -> result -> response pattern."""

    def __init__(
        self,
        request_mapper: IRequestMapper,
        result_mapper: IResultMapper[Any, TResponse],
        mediator: IMediator,
    ) -> None:
        self.request_mapper = request_mapper
        self.result_mapper = result_mapper
        self.mediator = mediator

    async def handle(self, request: Request, data: TRequest) -> TResponse:
        """
        Handle request using CQRS pattern:
        1. Map HTTP request to command/query
        2. Send command/query via mediator
        3. Map result to HTTP response
        """
        # Step 1: Request -> Command/Query
        command_or_query = await self.request_mapper.map_to_command_or_query(
            data, request
        )

        # Step 2: Command/Query -> Result (via mediator)
        # Use the unified send method - matches .NET ISender.Send()
        # Get cancellation token from request
        cancellation_token = CancellationToken(request)
        result = await self.mediator.send(command_or_query, cancellation_token)

        # Step 3: Result -> Response
        response = await self.result_mapper.map_to_response(result, request)

        return response


class CommandEndpoint(CQRSEndpoint[TRequest, TResponse], Generic[TRequest, TResponse]):
    """Endpoint specifically for handling commands."""

    def __init__(
        self,
        command_factory: type[ICommand[Any]],
        result_mapper: IResultMapper[Any, TResponse],
        mediator: IMediator,
    ) -> None:
        request_mapper: IRequestMapper = RequestToCommandMapper(command_factory)
        super().__init__(request_mapper, result_mapper, mediator)


class QueryEndpoint(CQRSEndpoint[TRequest, TResponse], Generic[TRequest, TResponse]):
    """Endpoint specifically for handling queries."""

    def __init__(
        self,
        query_factory: type[IQuery[Any]],
        result_mapper: IResultMapper[Any, TResponse],
        mediator: IMediator,
    ) -> None:
        request_mapper: IRequestMapper = RequestToQueryMapper(query_factory)
        super().__init__(request_mapper, result_mapper, mediator)


# Pagination support with CQRS
class PaginatedRequest(BaseRequest):
    """Base class for paginated requests."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(
        default=10, ge=1, le=100, description="Number of items per page"
    )

    @property
    def offset(self) -> int:
        """Calculate offset for pagination."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(DataResponse[list[TResult]], Generic[TResult]):
    """Base class for paginated responses."""

    total_count: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


class PaginatedResultToResponseMapper(
    IResultMapper[Any, PaginatedResponse[TResult]], Generic[TResult]
):
    """Maps paginated query results to paginated responses."""

    async def map_to_response(
        self, result: Any, original_request: Request  # noqa: ARG002
    ) -> PaginatedResponse[TResult]:
        """Map paginated result to paginated response."""
        # Assuming result has pagination information
        total_pages = (result.total_count + result.page_size - 1) // result.page_size

        return PaginatedResponse[TResult](
            data=result.data,
            total_count=result.total_count,
            page=result.page,
            page_size=result.page_size,
            total_pages=total_pages,
            message="Paginated data retrieved successfully",
        )


# Error handling for CQRS endpoints
class CQRSErrorHandler:
    """Handles errors in CQRS endpoints and maps them to appropriate responses."""

    @staticmethod
    async def handle_error(
        error: Exception, request: Request  # noqa: ARG004
    ) -> ErrorResponse:
        """Map exceptions to error responses."""
        if isinstance(error, ValueError):
            return ErrorResponse(
                message="Invalid request data",
                error_code="VALIDATION_ERROR",
                details={"error": str(error)},
            )
        elif isinstance(error, PermissionError):
            return ErrorResponse(
                message="Access denied",
                error_code="AUTHORIZATION_ERROR",
                details={"error": str(error)},
            )
        elif isinstance(error, FileNotFoundError):
            return ErrorResponse(
                message="Resource not found",
                error_code="NOT_FOUND",
                details={"error": str(error)},
            )
        else:
            return ErrorResponse(
                message="An unexpected error occurred",
                error_code="INTERNAL_ERROR",
                details={"error": str(error)},
            )


# Factory for creating CQRS endpoints
class CQRSEndpointFactory:
    """Factory for creating CQRS endpoints with proper configuration."""

    def __init__(self, mediator: IMediator) -> None:
        self.mediator = mediator

    def create_command_endpoint(
        self,
        command_factory: type[ICommand[Any]],
        result_mapper: IResultMapper[Any, Any] | None = None,
    ) -> CommandEndpoint[Any, Any]:
        """Create a command endpoint."""
        if result_mapper is None:
            result_mapper = ResultToBaseResponseMapper()

        return CommandEndpoint(command_factory, result_mapper, self.mediator)

    def create_query_endpoint(
        self,
        query_factory: type[IQuery[Any]],
        result_mapper: IResultMapper[Any, Any] | None = None,
    ) -> QueryEndpoint[Any, Any]:
        """Create a query endpoint."""
        if result_mapper is None:
            result_mapper = ResultToDataResponseMapper()

        return QueryEndpoint(query_factory, result_mapper, self.mediator)
