"""CQRS contracts matching .NET Shared.Contracts.CQRS interfaces."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

# Type variables for CQRS patterns
TResponse = TypeVar("TResponse")
TCommand = TypeVar("TCommand", bound="ICommand[Any]")
TQuery = TypeVar("TQuery", bound="IQuery[Any]")


class ICommand(BaseModel, Generic[TResponse], ABC):
    """Base command interface matching .NET ICommand<TResponse>."""

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class ICommandNoResponse(ICommand[None], ABC):
    """Command with no response, matching .NET ICommand (Unit response)."""

    pass


class IQuery(BaseModel, Generic[TResponse], ABC):
    """Base query interface matching .NET IQuery<T>."""

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class ICommandHandler(Generic[TCommand, TResponse], ABC):
    """Base command handler interface matching .NET ICommandHandler<TCommand, TResponse>."""

    @abstractmethod
    async def handle(self, command: TCommand) -> TResponse:
        """Handle the command asynchronously."""
        pass


class ICommandHandlerNoResponse(Generic[TCommand], ABC):
    """Command handler with no response matching .NET ICommandHandler<TCommand>."""

    @abstractmethod
    async def handle(self, command: TCommand) -> None:
        """Handle the command asynchronously with no return value."""
        pass


class IQueryHandler(Generic[TQuery, TResponse], ABC):
    """Base query handler interface matching .NET IQueryHandler<TQuery, TResponse>."""

    @abstractmethod
    async def handle(self, query: TQuery) -> TResponse:
        """Handle the query asynchronously."""
        pass
