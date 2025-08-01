"""Base CQRS classes for commands, queries, and handlers."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

TResult = TypeVar("TResult")


class ICommand(BaseModel, ABC):
    """Base interface for commands."""

    class Config:
        arbitrary_types_allowed = True


class IQuery(BaseModel, ABC):
    """Base interface for queries."""

    class Config:
        arbitrary_types_allowed = True


class ICommandHandler(ABC, Generic[TResult]):
    """Base interface for command handlers."""

    @abstractmethod
    async def handle(self, command: ICommand) -> TResult:
        """Handle a command."""
        pass


class IQueryHandler(ABC, Generic[TResult]):
    """Base interface for query handlers."""

    @abstractmethod
    async def handle(self, query: IQuery) -> TResult:
        """Handle a query."""
        pass


class CommandResult(BaseModel):
    """Result of a command execution."""

    success: bool
    message: str = ""
    data: Any = None

    class Config:
        arbitrary_types_allowed = True


class QueryResult(BaseModel, Generic[TResult]):
    """Result of a query execution."""

    success: bool
    data: TResult
    message: str = ""

    class Config:
        arbitrary_types_allowed = True
