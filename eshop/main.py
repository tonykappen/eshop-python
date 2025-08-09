"""Main FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from eshop.config.settings import settings
from eshop.core.auth.keycloak import KeycloakUser, add_keycloak_routes
from eshop.core.di.container import create_container, scan_assemblies, wire_container
from eshop.core.health.health_service import health_service
from eshop.core.logging.logger import configure_logging, get_logger
from eshop.core.logging.request_logging import add_request_logging_middleware
from eshop.core.middleware.auth_middleware import (
    add_auth_middleware,
    get_current_user_required,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger = get_logger("main")
    logger.info("Starting eShop Modular Monolith application")

    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        log_format="json",
        enable_seq=settings.log_enable_seq,
        seq_url=settings.seq_url,
        enable_file_logging=settings.log_enable_file,
        log_directory=settings.log_directory,
        separate_server_logs=settings.log_separate_server_logs,
    )

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
        ["eshop.modules.catalog", "eshop.modules.basket", "eshop.modules.ordering"],
    )

    # Wire container with packages
    wire_container(
        container,
        ["eshop.modules.catalog", "eshop.modules.basket", "eshop.modules.ordering"],
    )

    app.state.container = container

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down eShop Modular Monolith application")


# Create FastAPI app
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

# Add request logging middleware (before other middleware)
if settings.log_enable_request_logging:
    add_request_logging_middleware(
        app,
        log_request_body=settings.log_request_body,
        log_response_body=settings.log_response_body,
        exclude_health_checks=True,
    )


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
    user: KeycloakUser = Depends(get_current_user_required),
) -> dict[str, str | list[str]]:
    """Get current user information (requires authentication)."""
    return {
        "user_id": user.sub or "",
        "email": user.email or "",
        "name": user.name or "",
        "username": user.preferred_username or "",
        "roles": user.roles or [],
    }


# Import and include module routers
# Note: These will be added as modules are implemented
# from eshop.modules.catalog.api.router import router as catalog_router
# from eshop.modules.basket.api.router import router as basket_router
# from eshop.modules.ordering.api.router import router as ordering_router

# app.include_router(catalog_router, prefix="/api/v1/catalog", tags=["catalog"])
# app.include_router(basket_router, prefix="/api/v1/basket", tags=["basket"])
# app.include_router(ordering_router, prefix="/api/v1/ordering", tags=["ordering"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "eshop.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
