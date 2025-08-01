"""Pagination models using fastapi-pagination."""

from typing import Generic, TypeVar

from fastapi_pagination import Page, Params
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationRequest(BaseModel):
    """Pagination request model."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=10, ge=1, le=100, description="Page size")

    def to_params(self) -> Params:
        """Convert to fastapi-pagination Params."""
        return Params(page=self.page, size=self.size)


class PaginatedResult(BaseModel, Generic[T]):
    """Paginated result model."""

    items: list[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Page size")
    pages: int = Field(description="Total number of pages")

    @classmethod
    def from_page(cls, page: Page[T]) -> "PaginatedResult[T]":
        """Create PaginatedResult from fastapi-pagination Page."""
        return cls(
            items=page.items,
            total=page.total,
            page=page.page,
            size=page.size,
            pages=page.pages,
        )

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, size: int
    ) -> "PaginatedResult[T]":
        """Create PaginatedResult with calculated pages."""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(items=items, total=total, page=page, size=size, pages=pages)


class PaginationResponse(BaseModel, Generic[T]):
    """Standard pagination response wrapper."""

    data: PaginatedResult[T] = Field(description="Paginated data")
    success: bool = Field(default=True, description="Operation success status")
    message: str | None = Field(default=None, description="Response message")

    @classmethod
    def from_page(
        cls, page: Page[T], message: str | None = None
    ) -> "PaginationResponse[T]":
        """Create PaginationResponse from fastapi-pagination Page."""
        return cls(data=PaginatedResult.from_page(page), message=message)

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        size: int,
        message: str | None = None,
    ) -> "PaginationResponse[T]":
        """Create PaginationResponse with calculated pagination."""
        return cls(
            data=PaginatedResult.create(items, total, page, size), message=message
        )


# Convenience functions for pagination
def create_pagination_params(page: int = 1, size: int = 10) -> Params:
    """Create pagination parameters."""
    return Params(page=page, size=size)


def create_paginated_response(
    items: list[T], total: int, page: int, size: int, message: str | None = None
) -> PaginationResponse[T]:
    """Create a paginated response."""
    return PaginationResponse.create(items, total, page, size, message)
