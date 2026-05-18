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
from app.modules.basket.module_interface.router import (
    register_basket_module_with_fastapi,
)
from app.modules.catalog.module_interface.router import (
    register_catalog_module_with_fastapi,
)
from app.modules.ordering.module_interface.router import (
    register_ordering_module,
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


def _wire_module_lifecycle_hooks() -> None:
    """Wire module-specific messaging hooks into the lifecycle handler."""
    from app.modules.catalog.module_interface.catalog_bootstrap import CatalogModuleBootstrap

    catalog = CatalogModuleBootstrap()
    messaging_handler.add_startup_hook(catalog._startup_messaging)
    messaging_handler.add_shutdown_hook(catalog._shutdown_messaging)

    from app.core.messaging.outbox import register_outbox_orm

    outbox_orm = catalog.get_outbox_orm_class()
    if outbox_orm:
        register_outbox_orm(outbox_orm)


_wire_module_lifecycle_hooks()


# Include basket router with DI integration
# This will be called as a startup callback after mediator initialization
async def register_basket_router():
    """Register basket router with DI integration."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🔧 Registering basket router...")
    try:
        container = get_app_container()
        mediator = get_mediator()
        logger.info("Got container and mediator, calling register_basket_module_with_fastapi...")
        basket_router = register_basket_module_with_fastapi(app, container, mediator)
        logger.info(f"Basket router created with {len(basket_router.routes)} routes")
        app.include_router(basket_router)
        logger.info("✅ Basket router included successfully!")
        # Log all routes for debugging
        for route in basket_router.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', set())
                logger.info(f"  - {methods} {route.path}")
        print(f"✅ Successfully registered basket router with {len(basket_router.routes)} routes")
    except Exception as e:
        import traceback
        logger.error(f"❌ ERROR: Could not register basket router: {e}", exc_info=True)
        print(f"ERROR: Could not register basket router: {e}")
        traceback.print_exc()
        raise  # Re-raise to ensure the error is visible


# Include ordering router with DI integration
# This will be called as a startup callback after mediator initialization
async def register_ordering_router():
    """Register ordering router with DI integration."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🔧 Registering ordering router...")
    try:
        container = get_app_container()
        mediator = get_mediator()
        logger.info("Got container and mediator, calling register_ordering_module...")
        ordering_router = register_ordering_module(container, mediator)
        logger.info(f"Ordering router created with {len(ordering_router.routes)} routes")
        app.include_router(ordering_router)
        logger.info("✅ Ordering router included successfully!")
        # Log all routes for debugging
        for route in ordering_router.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', set())
                logger.info(f"  - {methods} {route.path}")
        print(f"✅ Successfully registered ordering router with {len(ordering_router.routes)} routes")
    except Exception as e:
        import traceback
        logger.error(f"❌ ERROR: Could not register ordering router: {e}", exc_info=True)
        print(f"ERROR: Could not register ordering router: {e}")
        traceback.print_exc()
        raise  # Re-raise to ensure the error is visible


# Register lifecycle callbacks for graceful startup and shutdown
register_startup_callback(initialize_logging)
register_startup_callback(initialize_dependency_injection)
register_startup_callback(initialize_mediator)
register_startup_callback(
    register_catalog_router
)  # Register catalog router after mediator is initialized
register_startup_callback(
    register_basket_router
)  # Register basket router after mediator is initialized
register_startup_callback(
    register_ordering_router
)  # Register ordering router after mediator is initialized
print("DEBUG: Registered all startup callbacks including register_basket_router and register_ordering_router")


async def subscribe_basket_handlers():
    """Subscribe basket integration event handlers to the shared message bus."""
    from app.modules.basket.module_interface.router import (
        subscribe_basket_handlers_to_message_bus,
    )

    await subscribe_basket_handlers_to_message_bus()
    print("✅ Subscribed basket handlers to message bus")


register_startup_callback(subscribe_basket_handlers)


# Subscribe ordering handlers to message bus after basket (both before outbox worker)
async def subscribe_ordering_handlers():
    """Subscribe ordering integration event handlers to message bus."""
    from app.modules.ordering.module_interface.router import (
        subscribe_ordering_handlers_to_message_bus,
    )
    await subscribe_ordering_handlers_to_message_bus()
    print("✅ Subscribed ordering handlers to message bus")

register_startup_callback(subscribe_ordering_handlers)

# Start basket outbox publisher worker after handlers are subscribed
# (so handlers are ready before worker starts processing)
async def start_basket_outbox_worker():
    """Start the basket outbox publisher worker."""
    from app.modules.basket.workers.outbox_publisher_worker import (
        basket_outbox_publisher_worker,
    )
    await basket_outbox_publisher_worker.start()
    print("✅ Started basket outbox publisher worker")

register_startup_callback(start_basket_outbox_worker)

register_startup_callback(database_handler.startup)
register_startup_callback(register_outbox_workers)  # Before messaging so workers exist for start_all()
register_startup_callback(cache_handler.startup)
register_startup_callback(messaging_handler.startup)
register_startup_callback(auth_handler.startup)
register_startup_callback(health_handler.startup)

# Register shutdown callbacks (executed in reverse order)
async def stop_basket_outbox_worker():
    """Stop the basket outbox publisher worker."""
    from app.modules.basket.workers.outbox_publisher_worker import (
        basket_outbox_publisher_worker,
    )
    await basket_outbox_publisher_worker.stop()
    print("✅ Stopped basket outbox publisher worker")

register_shutdown_callback(stop_basket_outbox_worker)


async def stop_ordering_message_bus():
    """Disconnect the ordering RabbitMQ message bus on shutdown."""
    from app.modules.ordering.module_interface.di.orders import (
        get_ordering_message_bus,
    )

    message_bus = get_ordering_message_bus()
    if hasattr(message_bus, "disconnect"):
        try:
            await message_bus.disconnect()
            print("✅ Disconnected ordering message bus")
        except Exception as exc:  # noqa: BLE001 - log + swallow on shutdown
            print(f"⚠️ Failed to disconnect ordering message bus: {exc}")


register_shutdown_callback(stop_ordering_message_bus)


async def stop_basket_message_bus():
    """Disconnect the basket outbox RabbitMQ message bus on shutdown."""
    from app.modules.basket.workers.outbox_publisher_worker import (
        _get_basket_message_bus,
    )

    message_bus = _get_basket_message_bus()
    if hasattr(message_bus, "disconnect"):
        try:
            await message_bus.disconnect()
            print("✅ Disconnected basket outbox message bus")
        except Exception as exc:  # noqa: BLE001 - log + swallow on shutdown
            print(f"⚠️ Failed to disconnect basket outbox message bus: {exc}")


register_shutdown_callback(stop_basket_message_bus)
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
