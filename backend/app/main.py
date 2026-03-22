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
from app.core.mediator.fastapi_integration import get_mediator
from app.core.middleware.auth_middleware import add_auth_middleware
from app.core.middleware.metrics_middleware import add_metrics_middleware
from app.core.middleware.tracing_middleware import add_tracing_middleware
from app.module_interface.router import create_root_router
from app.modules.catalog.module_interface.router import (
    register_catalog_module_with_fastapi,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager with graceful startup and shutdown."""
    # Set shutdown timeout for production deployment
    lifecycle_manager.set_shutdown_timeout(60.0)  # 60 seconds for graceful shutdown

    # Store container and mediator on app.state (Phase 1.7)
    container = get_app_container()
    if container:
        app.state.container = container

    from app.core.mediator.fastapi_integration import store_mediator_on_app
    store_mediator_on_app(app)

    # Update auth handler with app instance before startup
    set_app_instance(app)

    # Use the comprehensive lifecycle manager
    async with lifecycle_manager.lifespan_context(app):
        # Add Keycloak routes after auth handler startup
        try:
            from app.core.auth.keycloak import add_keycloak_routes

            add_keycloak_routes(app)
        except Exception as e:
            print(f"Warning: Could not add Keycloak routes: {e}")

        yield


# Include catalog router with DI integration
# This will be called as a startup callback after mediator initialization
async def register_catalog_router():
    """Register catalog router with DI integration."""
    try:
        container = get_app_container()
        mediator = get_mediator()
        catalog_router = register_catalog_module_with_fastapi(app, container, mediator)
        app.include_router(catalog_router)
    except Exception as e:
        print(f"Error: Could not register catalog router: {e}")
        raise


async def register_outbox_workers():
    """Register all module outbox workers explicitly (composition root). Runs after DB startup."""
    try:
        from app.modules.catalog.outbox_registration import register_outbox_worker as register_catalog_outbox

        register_catalog_outbox()
    except Exception as e:
        print(f"Error: Could not register outbox workers: {e}")
        raise


# Register lifecycle callbacks for graceful startup and shutdown
register_startup_callback(initialize_logging)
register_startup_callback(initialize_dependency_injection)
register_startup_callback(initialize_mediator)
register_startup_callback(
    register_catalog_router
)  # Register catalog router after mediator is initialized
register_startup_callback(database_handler.startup)
register_startup_callback(register_outbox_workers)  # Before messaging so workers exist for start_all()
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

# App instance will be set in the lifespan function

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMPORTANT: FastAPI middleware executes in REVERSE order of registration (LIFO)
# Execution order (what we want):
# 1. Tracing middleware (captures all requests with OTEL spans) - runs FIRST
# 2. Metrics middleware (measures all requests) - runs SECOND
# 3. Auth middleware (sets request.state.user) - runs THIRD
# 4. CLEF logging middleware (uses user context from auth) - runs LAST
#
# Registration order (add in reverse):
# 1. CLEF logging (added first, executes last)
# 2. Auth (added second, executes third)
# 3. Metrics (added third, executes second)
# 4. Tracing (added last, executes first)

# Add CLEF request/response logging middleware FIRST (executes LAST)
# This ensures it runs AFTER auth middleware (which sets request.state.user)
if settings.log_enable_request_logging:
    add_clef_logging_middleware(
        app,
        exclude_health_checks=True,
    )

# Add authentication middleware SECOND (executes THIRD, sets request.state.user)
add_auth_middleware(app)

# Add metrics middleware THIRD (executes SECOND, measures request counts and latency)
add_metrics_middleware(
    app,
    service_name="eshop-api",
    exclude_health_checks=True,
)

# Add tracing middleware LAST (executes FIRST, captures everything)
# Extracts traceparent + baggage, starts OTEL span
add_tracing_middleware(
    app,
    service_name="eshop-api",
    exclude_health_checks=True,
)

# Note: Keycloak routes will be added lazily after Keycloak setup is complete
# This prevents the race condition where routes are added before the realm exists

# Add pagination support
add_pagination(app)

# Add custom exception handlers
add_exception_handlers(app)

# Include root router from global module_interface (includes health)
root_router = create_root_router()
app.include_router(root_router)

app.include_router(auth_proxy_router, prefix="/api/v1", tags=["auth-proxy"])
# Health router is now included via root_router, but keeping for backward compatibility
app.include_router(health_router)


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
