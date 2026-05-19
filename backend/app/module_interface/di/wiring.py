"""Wire DI into FastAPI lifespan."""

from app.core.initialization import (cleanup_dependency_injection,
                                     get_app_container)
from fastapi import FastAPI


def wire_di_to_fastapi(app: FastAPI) -> None:
    """
    Wire dependency injection into FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Store container reference in app state
    container = get_app_container()
    if container:
        app.state.container = container


def initialize_di() -> None:
    """Initialize dependency injection (called during startup)."""
    # This is handled by the lifecycle manager in main.py
    # But we can add module-specific DI initialization here if needed
    pass


async def cleanup_di() -> None:
    """Cleanup dependency injection (called during shutdown)."""
    # This is handled by the lifecycle manager in main.py
    await cleanup_dependency_injection()
