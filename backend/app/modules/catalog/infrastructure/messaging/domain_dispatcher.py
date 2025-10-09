"""In-memory domain event dispatcher."""

import logging
from typing import Any, Callable, Dict, List, Type

from app.core.domain.events import DomainEvent

logger = logging.getLogger(__name__)


class DomainEventDispatcher:
    """In-memory domain event dispatcher."""

    def __init__(self):
        """Initialize the domain event dispatcher."""
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = {}

    def register_handler(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        """
        Register a handler for a domain event type.
        
        Args:
            event_type: Type of domain event
            handler: Handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type.__name__}")

    def unregister_handler(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        """
        Unregister a handler for a domain event type.
        
        Args:
            event_type: Type of domain event
            handler: Handler function
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Unregistered handler for event type: {event_type.__name__}")

    async def dispatch(self, event: DomainEvent) -> None:
        """
        Dispatch a domain event to all registered handlers.
        
        Args:
            event: Domain event to dispatch
        """
        event_type = type(event)
        
        if event_type not in self._handlers:
            logger.debug(f"No handlers registered for event type: {event_type.__name__}")
            return
        
        handlers = self._handlers[event_type]
        logger.debug(f"Dispatching event {event_type.__name__} to {len(handlers)} handlers")
        
        for handler in handlers:
            try:
                if hasattr(handler, 'handle'):
                    await handler.handle(event)
                else:
                    await handler(event)
            except Exception as e:
                logger.error(f"Error in domain event handler: {e}")
                # Continue with other handlers even if one fails

    async def dispatch_all(self, events: List[DomainEvent]) -> None:
        """
        Dispatch multiple domain events.
        
        Args:
            events: List of domain events to dispatch
        """
        for event in events:
            await self.dispatch(event)

    def get_handlers(self, event_type: Type[DomainEvent]) -> List[Callable]:
        """
        Get all handlers for an event type.
        
        Args:
            event_type: Type of domain event
            
        Returns:
            List of handlers
        """
        return self._handlers.get(event_type, []).copy()

    def get_registered_event_types(self) -> List[Type[DomainEvent]]:
        """
        Get all registered event types.
        
        Returns:
            List of registered event types
        """
        return list(self._handlers.keys())

    def clear_handlers(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
        logger.info("Cleared all domain event handlers")


# Global dispatcher instance
domain_event_dispatcher = DomainEventDispatcher()


