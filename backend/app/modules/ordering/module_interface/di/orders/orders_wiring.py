"""Ordering module DI wiring."""

import logging

from app.core.di.container import Container
from app.core.mediator.mediator import Mediator

logger = logging.getLogger(__name__)


def register_ordering_handlers_with_mediator(mediator: Mediator) -> None:
    """
    Register ordering handlers with mediator.

    Args:
        mediator: Mediator instance
    """
    from app.core.mediator.handler_registry import HandlerRegistry
    from app.modules.ordering.application.ordering_handler_registration import (
        register_ordering_handlers,
    )

    handler_registry = mediator.handler_registry
    register_ordering_handlers(handler_registry)
    logger.info("Registered ordering handlers with mediator")


def wire_ordering_dependencies(container: Container) -> None:
    """
    Wire ordering module dependencies.

    Args:
        container: DI container
    """
    # Wire repositories, handlers, etc.
    # This is a placeholder - can be extended with actual wiring
    logger.info("Wired ordering dependencies")


def wire_ordering_dependencies_to_fastapi(
    app, container: Container, mediator: Mediator
) -> None:
    """
    Wire ordering dependencies to FastAPI app.

    Args:
        app: FastAPI app
        container: DI container
        mediator: Mediator instance
    """
    # This is a placeholder - actual wiring will be done via FastAPI DI
    # Handlers will be created per-request with dependencies injected
    logger.info("Wired ordering dependencies to FastAPI")
