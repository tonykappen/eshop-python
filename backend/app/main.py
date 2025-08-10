"""Main FastAPI application entry point with graceful startup and shutdown."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.config.settings import settings
from app.core.auth.keycloak import KeycloakUser, add_keycloak_routes, get_current_user
from app.core.di.container import create_container, scan_assemblies, wire_container
from app.core.exceptions.handler import add_exception_handlers
from app.core.health.health_service import health_service
from app.core.lifecycle.handlers import (
    auth_handler,
    cache_handler,
    database_handler,
    health_handler,
    messaging_handler,
)
from app.core.lifecycle.manager import (
    lifecycle_manager,
    register_shutdown_callback,
    register_startup_callback,
)
from app.core.logging.logger import configure_logging, get_logger
from app.core.logging.request_logging import add_request_logging_middleware
from app.core.mediator.fastapi_integration import configure_mediator
from app.core.middleware.auth_middleware import add_auth_middleware
from app.modules.catalog.api.router import router as catalog_router


async def configure_application_startup() -> None:
    """Configure application startup sequence."""
    logger = get_logger("main")
    logger.info("Configuring eShop Modular Monolith application")

    # Configure logging first
    configure_logging(
        log_level=settings.log_level,
        log_format="json",
        enable_seq=settings.log_enable_seq,
        seq_url=settings.seq_url,
        enable_file_logging=settings.log_enable_file,
        log_directory=settings.log_directory,
        separate_server_logs=settings.log_separate_server_logs,
    )

    logger.info("Logging configuration completed")


async def initialize_dependency_injection() -> None:
    """Initialize dependency injection container."""
    logger = get_logger("main")
    logger.info("Initializing dependency injection container")

    # Initialize DI container
    container = create_container()
    container.config.from_dict(
        {
            "database": {"connection_string": settings.database_connection_string},
            "redis": {"connection_string": settings.redis_connection_string},
            "rabbitmq": {"connection_string": settings.rabbitmq_connection_string},
            "keycloak": {
                "server_url": settings.keycloak_server_url,
                "realm": settings.keycloak_realm,
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
            },
        }
    )

    # Scan assemblies for automatic service registration
    scan_assemblies(
        container,
        ["app.modules.catalog", "app.modules.basket", "app.modules.ordering"],
    )

    # Wire container with packages (after services are registered)
    try:
        wire_container(
            container,
            ["app.modules.catalog", "app.modules.basket", "app.modules.ordering"],
        )
    except Exception as e:
        logger.warning(f"Container wiring failed (non-critical): {e}")
        # Continue without wiring - services can still be accessed directly

    # Store container in application state
    # This will be set when the app is created
    global _app_container
    _app_container = container

    logger.info("Dependency injection container initialized")


async def initialize_mediator() -> None:
    """Initialize mediator pattern - matches .NET AddMediatRWithAssemblies()."""
    logger = get_logger("main")
    logger.info("Initializing mediator pattern")

    # Configure mediator (matches .NET Program.cs configuration)
    configure_mediator()

    logger.info("Mediator pattern initialized")


async def cleanup_dependency_injection() -> None:
    """Cleanup dependency injection container."""
    logger = get_logger("main")
    logger.info("Cleaning up dependency injection container")

    global _app_container
    if _app_container:
        # Perform any necessary cleanup
        # container.unwire()
        logger.info("Dependency injection container cleanup completed")


# Global container reference for lifecycle management
_app_container = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager with graceful startup and shutdown."""
    # Set shutdown timeout for production deployment
    lifecycle_manager.set_shutdown_timeout(60.0)  # 60 seconds for graceful shutdown

    # Store container reference in app state for access in routes
    global _app_container
    if _app_container:
        app.state.container = _app_container

    # Use the comprehensive lifecycle manager
    async with lifecycle_manager.lifespan_context(app):
        yield


# Register lifecycle callbacks for graceful startup and shutdown
register_startup_callback(configure_application_startup)
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

# Create FastAPI app with graceful lifecycle management
app = FastAPI(
    title=settings.name,
    version=settings.version,
    description="Modular Monolith eShop migrated from .NET to Python (FastAPI)",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Keycloak authentication routes
add_keycloak_routes(app)

# Add authentication middleware
add_auth_middleware(app)

# Add pagination support
add_pagination(app)

# Add custom exception handlers
add_exception_handlers(app)

# Add request logging middleware (before other middleware)
if settings.log_enable_request_logging:
    add_request_logging_middleware(
        app,
        log_request_body=settings.log_request_body,
        log_response_body=settings.log_response_body,
        exclude_health_checks=True,
    )

# from app.modules.basket.api.router import router as basket_router
# from app.modules.ordering.api.router import router as ordering_router

print("🔧 Including catalog router...")
app.include_router(catalog_router, prefix="/api/v1", tags=["catalog"])
print("✅ Catalog router included successfully - RBAC ready!")

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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.version,
        "timestamp": "2024-01-01T00:00:00Z",
    }


@app.get("/api/v1/health")
async def api_health_check() -> dict[str, str | list[str]]:
    """API health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1",
        "modules": ["catalog", "basket", "ordering"],
    }


@app.get("/health/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """Detailed health check for all services."""
    return await health_service.check_all_services()


@app.get("/health/database")
async def database_health_check() -> dict[str, Any]:
    """Database health check endpoint."""
    return await health_service.check_database()


@app.get("/health/redis")
async def redis_health_check() -> dict[str, Any]:
    """Redis health check endpoint."""
    return await health_service.check_redis()


@app.get("/health/rabbitmq")
async def rabbitmq_health_check() -> dict[str, Any]:
    """RabbitMQ health check endpoint."""
    return await health_service.check_rabbitmq()


@app.get("/health/keycloak")
async def keycloak_health_check() -> dict[str, Any]:
    """Keycloak health check endpoint."""
    return await health_service.check_keycloak()


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
