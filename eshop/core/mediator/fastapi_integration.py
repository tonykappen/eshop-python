"""FastAPI integration for mediator pattern with 1-1 parity to .NET."""

from typing import Any

from fastapi import Request

from .cancellation import CancellationToken, get_cancellation_token
from .handler_registry import HandlerRegistry
from .mediator import Mediator

# Global services container (simplified version of .NET IServiceCollection)
_services: dict[str, Any] = {}


def configure_mediator() -> None:
    """Configure mediator for FastAPI - matches .NET Program.cs configuration."""
    # Create handler registry
    handler_registry = HandlerRegistry()

    # Create mediator
    mediator = Mediator(handler_registry)

    # Register in services
    _services["mediator"] = mediator
    _services["handler_registry"] = handler_registry


def get_mediator() -> Mediator:
    """Get mediator dependency - matches .NET ISender dependency injection."""
    mediator = _services.get("mediator")
    if not mediator:
        raise RuntimeError("Mediator not configured. Call configure_mediator() first.")
    return mediator  # type: ignore


def get_handler_registry() -> HandlerRegistry:
    """Get handler registry dependency."""
    registry = _services.get("handler_registry")
    if not registry:
        raise RuntimeError(
            "Handler registry not configured. Call configure_mediator() first."
        )
    return registry  # type: ignore


# FastAPI dependency functions
def get_mediator_dependency() -> Mediator:
    """FastAPI dependency for mediator."""
    return get_mediator()


def get_handler_registry_dependency() -> HandlerRegistry:
    """FastAPI dependency for handler registry."""
    return get_handler_registry()


def get_cancellation_token_dependency(request: Request) -> CancellationToken:
    """FastAPI dependency for cancellation token - matches .NET CancellationToken injection."""
    return get_cancellation_token(request)
