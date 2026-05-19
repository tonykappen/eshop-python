"""In-memory domain event dispatcher."""

from typing import Any

from app.core.domain.events import DomainEvent
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class DomainEventDispatcher:
    """In-memory domain event dispatcher."""

    def __init__(self):
        """Initialize the domain event dispatcher."""
        self._handlers: dict[type[DomainEvent], list[Any]] = {}

    def register_handler(
        self, event_type: type[DomainEvent], handler: Any
    ) -> None:
        """
        Register a handler for a domain event type.

        Args:
            event_type: Type of domain event
            handler: Handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.log_debug_with_context(
            "Registered handler for event type",
            context={"event_type": event_type.__name__},
        )

    def unregister_handler(
        self, event_type: type[DomainEvent], handler: Any
    ) -> None:
        """
        Unregister a handler for a domain event type.

        Args:
            event_type: Type of domain event
            handler: Handler function
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.log_debug_with_context(
                "Unregistered handler for event type",
                context={"event_type": event_type.__name__},
            )

    async def dispatch(self, event: DomainEvent) -> None:
        """
        Dispatch a domain event to all registered handlers.

        Args:
            event: Domain event to dispatch
        """
        event_type = type(event)

        if event_type not in self._handlers:
            logger.log_debug_with_context(
                "No handlers registered for event type",
                context={"event_type": event_type.__name__},
            )
            return

        handlers = self._handlers[event_type]
        logger.log_debug_with_context(
            "Dispatching event to handlers",
            context={"event_type": event_type.__name__, "handler_count": len(handlers)},
        )

        for handler in handlers:
            try:
                if hasattr(handler, "handle"):
                    await handler.handle(event)
                else:
                    await handler(event)
            except Exception as e:
                logger.log_error_with_context(
                    "Error in domain event handler",
                    error=e,
                    context={"event_type": event_type.__name__},
                )
                # Continue with other handlers even if one fails

    async def dispatch_all(self, events: list[DomainEvent]) -> None:
        """
        Dispatch multiple domain events.

        Args:
            events: List of domain events to dispatch
        """
        for event in events:
            await self.dispatch(event)

    def get_handlers(self, event_type: type[DomainEvent]) -> list[Any]:
        """
        Get all handlers for an event type.

        Args:
            event_type: Type of domain event

        Returns:
            List of handlers
        """
        return self._handlers.get(event_type, []).copy()

    def get_registered_event_types(self) -> list[type[DomainEvent]]:
        """
        Get all registered event types.

        Returns:
            List of registered event types
        """
        return list(self._handlers.keys())

    def clear_handlers(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
        logger.log_with_context("Cleared all domain event handlers")


# Global dispatcher instance
domain_event_dispatcher = DomainEventDispatcher()
