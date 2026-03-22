"""FastAPI integration for mediator pattern with 1-1 parity to .NET."""

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mediator.cancellation import (
    CancellationToken,
    get_cancellation_token,
    get_cancellation_token_with_session,
)
from app.core.mediator.handler_registry import HandlerRegistry
from app.core.mediator.mediator import Mediator

_services: dict[str, Any] = {}


def configure_mediator(module_bootstraps: list[Any] | None = None) -> None:
    """Configure mediator for FastAPI.

    Args:
        module_bootstraps: Optional list of IModuleBootstrap instances.
            If provided, handler registration is delegated to each module.
            If not provided, falls back to direct catalog import for backward compat.
    """
    handler_registry = HandlerRegistry()

    if module_bootstraps:
        for bootstrap in module_bootstraps:
            bootstrap.register_handlers(handler_registry)
    else:
        _register_module_handlers(handler_registry)

    mediator = Mediator(handler_registry)

    _services["mediator"] = mediator
    _services["handler_registry"] = handler_registry


def store_mediator_on_app(app) -> None:
    """Move mediator/registry to app.state so they are app-scoped, not module-global."""
    mediator = _services.get("mediator")
    handler_registry = _services.get("handler_registry")
    if mediator:
        app.state.mediator = mediator
    if handler_registry:
        app.state.handler_registry = handler_registry


def _register_module_handlers(handler_registry: HandlerRegistry) -> None:
    from app.modules.catalog.module_interface.catalog_handler_registration import (
        register_catalog_handlers,
    )
    register_catalog_handlers(handler_registry)


def get_mediator(app=None) -> Mediator:
    """Get mediator — prefers app.state, falls back to module dict."""
    if app is not None and hasattr(app, "state") and hasattr(app.state, "mediator"):
        return app.state.mediator
    mediator = _services.get("mediator")
    if not mediator:
        raise RuntimeError("Mediator not configured. Call configure_mediator() first.")
    return mediator


def get_handler_registry(app=None) -> HandlerRegistry:
    if app is not None and hasattr(app, "state") and hasattr(app.state, "handler_registry"):
        return app.state.handler_registry
    registry = _services.get("handler_registry")
    if not registry:
        raise RuntimeError("Handler registry not configured. Call configure_mediator() first.")
    return registry


def get_mediator_dependency() -> Mediator:
    """FastAPI dependency for mediator."""
    return get_mediator()


def get_handler_registry_dependency() -> HandlerRegistry:
    """FastAPI dependency for handler registry."""
    return get_handler_registry()


def get_cancellation_token_dependency(request: Request) -> CancellationToken:
    """FastAPI dependency for cancellation token."""
    return get_cancellation_token(request)


def get_cancellation_token_with_session_dependency(
    request: Request, session: AsyncSession
) -> CancellationToken:
    """FastAPI dependency for cancellation token with database session."""
    return get_cancellation_token_with_session(request, session)
