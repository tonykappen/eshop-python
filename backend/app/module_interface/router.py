"""Root API router that mounts modules + health."""

from fastapi import APIRouter

from app.module_interface.health import health_router


def create_root_router() -> APIRouter:
    """
    Create the root API router that mounts all modules and health endpoints.

    Returns:
        Root API router
    """
    router = APIRouter()

    # Mount health endpoints
    router.include_router(health_router)

    # Module routers will be added by main.py via their registration functions
    # This keeps the router clean and allows modules to register themselves

    return router


__all__ = ["create_root_router"]
