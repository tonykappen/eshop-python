"""Shared message bus instance for cross-module communication."""

from app.core.messaging.bus import InMemoryMessageBus

# Global shared message bus instance
# This allows different modules to publish and subscribe to events
_shared_message_bus: InMemoryMessageBus | None = None


def get_shared_message_bus() -> InMemoryMessageBus:
    """
    Get the shared message bus instance.

    Returns:
        Shared InMemoryMessageBus instance
    """
    global _shared_message_bus
    if _shared_message_bus is None:
        _shared_message_bus = InMemoryMessageBus()
    return _shared_message_bus


def reset_shared_message_bus() -> None:
    """Reset the shared message bus (useful for testing)."""
    global _shared_message_bus
    _shared_message_bus = None
