"""Main FastAPI application entry point with graceful startup and shutdown."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.api.auth_proxy import router as auth_proxy_router
from app.config.settings import settings
from app.core.auth.keycloak import KeycloakUser, get_current_user
from app.core.exceptions.handler import add_exception_handlers
from app.core.health.health_endpoints import health_router
from app.core.initialization import (
    cleanup_dependency_injection,
    get_app_container,
    initialize_dependency_injection,
    initialize_logging,
    initialize_mediator,
    shutdown_logging,
)
from app.core.lifecycle.handlers import (
    auth_handler,
    cache_handler,
    database_handler,
    health_handler,
    messaging_handler,
    set_app_instance,
)
from app.core.lifecycle.manager import (
    lifecycle_manager,
    register_shutdown_callback,
    register_startup_callback,
)
from app.core.logging.clef_middleware import add_clef_logging_middleware
from app.core.middleware.auth_middleware import add_auth_middleware
from app.modules.catalog.api.router import router as catalog_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager with graceful startup and shutdown."""
    # Set shutdown timeout for production deployment
    lifecycle_manager.set_shutdown_timeout(60.0)  # 60 seconds for graceful shutdown

    # Store container reference in app state for access in routes
    container = get_app_container()
    if container:
        app.state.container = container

    # Use the comprehensive lifecycle manager
    async with lifecycle_manager.lifespan_context(app):
        yield


# Register lifecycle callbacks for graceful startup and shutdown
register_startup_callback(initialize_logging)
register_startup_callback(initialize_dependency_injection)
register_startup_callback(initialize_mediator)
register_startup_callback(database_handler.startup)
register_startup_callback(cache_handler.startup)
register_startup_callback(messaging_handler.startup)
register_startup_callback(auth_handler.startup)
register_startup_callback(health_handler.startup)

# Register shutdown callbacks (executed in reverse order)
register_shutdown_callback(cleanup_dependency_injection)
register_shutdown_callback(database_handler.shutdown)
register_shutdown_callback(cache_handler.shutdown)
register_shutdown_callback(messaging_handler.shutdown)
register_shutdown_callback(auth_handler.shutdown)
register_shutdown_callback(health_handler.shutdown)
register_shutdown_callback(
    shutdown_logging
)  # Shutdown logging last to capture all events

# Create FastAPI app with graceful lifecycle management
app = FastAPI(
    title=settings.name,
    version=settings.version,
    description="Modular Monolith eShop migrated from .NET to Python (FastAPI)",
    lifespan=lifespan,
)

# Set the app instance for lifecycle handlers that need it
set_app_instance(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
add_auth_middleware(app)

# Note: Keycloak routes will be added lazily after Keycloak setup is complete
# This prevents the race condition where routes are added before the realm exists

# Add pagination support
add_pagination(app)

# Add custom exception handlers
add_exception_handlers(app)

# Add CLEF request/response logging middleware (before other middleware)
if settings.log_enable_request_logging:
    add_clef_logging_middleware(
        app,
        exclude_health_checks=True,
    )

# from app.modules.basket.api.router import router as basket_router
# from app.modules.ordering.api.router import router as ordering_router

# Include catalog router
app.include_router(catalog_router, prefix="/api/v1", tags=["catalog"])
app.include_router(auth_proxy_router, prefix="/api/v1", tags=["auth-proxy"])
app.include_router(health_router)

# app.include_router(basket_router, prefix="/api/v1/basket", tags=["basket"])
# app.include_router(ordering_router, prefix="/api/v1/ordering", tags=["ordering"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "eShop Modular Monolith API",
        "version": settings.version,
        "status": "running",
    }


@app.get("/api/v1/auth/me")
async def get_current_user_info(
    user: KeycloakUser = Depends(get_current_user),
) -> dict[str, str | list[str]]:
    """Get current user information (requires authentication)."""
    return {
        "user_id": user.sub or "",
        "email": user.email or "",
        "name": user.name or "",
        "username": user.preferred_username or "",
        "roles": user.roles or [],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
