"""Central mediator - wrapper around core mediator."""

from app.core.mediator.handler_registry import HandlerRegistry
from app.core.mediator.mediator import IMediator
from app.core.mediator.mediator import Mediator as CoreMediator

__all__ = ["Mediator", "IMediator"]


class Mediator(CoreMediator):
    """Central mediator for the application."""

    def __init__(self, handler_registry: HandlerRegistry | None = None) -> None:
        """
        Initialize the mediator.

        Args:
            handler_registry: Handler registry (creates new one if not provided)
        """
        if handler_registry is None:
            handler_registry = HandlerRegistry()
        super().__init__(handler_registry)
