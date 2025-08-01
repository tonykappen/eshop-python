"""Base REPR (Request-Endpoint-Response) pattern classes."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from fastapi import Request
from pydantic import BaseModel

TRequest = TypeVar("TRequest", bound=BaseModel)
TResponse = TypeVar("TResponse", bound=BaseModel)


class BaseRequest(BaseModel):
    """Base request class for REPR pattern."""

    class Config:
        arbitrary_types_allowed = True


class BaseResponse(BaseModel):
    """Base response class for REPR pattern."""

    success: bool = True
    message: str = ""

    class Config:
        arbitrary_types_allowed = True


class Endpoint(ABC, Generic[TRequest, TResponse]):
    """Base endpoint class following REPR pattern."""

    @abstractmethod
    async def handle(self, request: Request, data: TRequest) -> TResponse:
        """Handle the endpoint request."""
        pass

    async def check_disconnection(self, request: Request) -> bool:
        """Check if client has disconnected (collection token pattern)."""
        return request.is_disconnected()

    async def execute(self, request: Request, data: TRequest) -> TResponse:
        """Execute the endpoint with disconnection check."""
        if await self.check_disconnection(request):
            raise ConnectionError("Client disconnected")

        return await self.handle(request, data)


class PaginatedRequest(BaseRequest):
    """Base class for paginated requests."""

    page: int = 1
    page_size: int = 10

    @property
    def offset(self) -> int:
        """Calculate offset for pagination."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseResponse, Generic[TResponse]):
    """Base class for paginated responses."""

    data: list[TResponse] = []
    total_count: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1
