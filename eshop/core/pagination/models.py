"""Pagination models."""

from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginationRequest(BaseModel):
    """Pagination request model."""
    
    page: int = 1
    page_size: int = 10
    
    @property
    def offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get the limit for database queries."""
        return self.page_size


class PaginatedResult(BaseModel, Generic[T]):
    """Paginated result model."""
    
    data: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1
    
    @classmethod
    def create(cls, data: List[T], total_count: int, page: int, page_size: int) -> "PaginatedResult[T]":
        """Create a paginated result."""
        total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
        
        return cls(
            data=data,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        ) 