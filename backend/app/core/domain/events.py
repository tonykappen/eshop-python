"""Domain events module."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.core.domain.entity import DomainEvent

TEvent = TypeVar("TEvent", bound=DomainEvent)

__all__ = ["DomainEvent", "DomainEventHandler"]


class DomainEventHandler(ABC, Generic[TEvent]):
    """Base class for domain event handlers."""

    @abstractmethod
    async def handle(self, event: TEvent) -> None:
        """
        Handle a domain event.
        
        Args:
            event: The domain event to handle
        """
        pass
