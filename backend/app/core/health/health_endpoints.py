"""Health check endpoints for eShop Modular Monolith."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.config.settings import settings
from app.core.health.health_service import health_service

# Create router for health endpoints
health_router = APIRouter()


@health_router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@health_router.get("/api/v1/health")
async def api_health_check() -> dict[str, str | list[str]]:
    """API health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1",
        "modules": ["catalog", "basket", "ordering"],
    }


@health_router.get("/health/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """Detailed health check for all services."""
    return await health_service.check_all_services()


@health_router.get("/health/database")
async def database_health_check() -> dict[str, Any]:
    """Database health check endpoint."""
    return await health_service.check_database()


@health_router.get("/health/redis")
async def redis_health_check() -> dict[str, Any]:
    """Redis health check endpoint."""
    return await health_service.check_redis()


@health_router.get("/health/rabbitmq")
async def rabbitmq_health_check() -> dict[str, Any]:
    """RabbitMQ health check endpoint."""
    return await health_service.check_rabbitmq()


@health_router.get("/health/keycloak")
async def keycloak_health_check() -> dict[str, Any]:
    """Keycloak health check endpoint."""
    return await health_service.check_keycloak()


@health_router.get("/health/seq")
async def seq_health_check() -> dict[str, Any]:
    """Seq logging health check endpoint."""
    return await health_service.check_seq()
