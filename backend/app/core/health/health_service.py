"""Health check service for all infrastructure components."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import asyncpg
import redis.asyncio as redis
from faststream.rabbit import RabbitBroker

from app.config.settings import settings
from app.core.auth.keycloak import keycloak_service
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class HealthService:
    """Health check service for all infrastructure components."""

    def __init__(self) -> None:
        """Initialize health service."""
        self.redis_client = None
        self.db_pool = None
        self.rabbit_broker = None

    async def check_database(self) -> dict[str, Any]:
        """Check database connectivity."""
        try:
            # Create connection pool for health check
            pool = await asyncpg.create_pool(
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                database=settings.db_name,
                min_size=1,
                max_size=5,
            )

            # Test connection
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")

            await pool.close()

            return {
                "status": "healthy",
                "service": "database",
                "host": settings.db_host,
                "port": settings.db_port,
                "database": settings.db_name,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            logger.log_error_with_context(
                "Database health check failed",
                error=e,
                context={
                    "service": "database",
                    "host": settings.db_host,
                    "port": settings.db_port
                }
            )
            return {
                "status": "unhealthy",
                "service": "database",
                "error": str(e),
                "host": settings.db_host,
                "port": settings.db_port,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def check_redis(self) -> dict[str, Any]:
        """Check Redis connectivity."""
        try:
            # Create async Redis client
            redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
            )

            # Test connection
            await redis_client.ping()
            await redis_client.close()

            return {
                "status": "healthy",
                "service": "redis",
                "host": settings.redis_host,
                "port": settings.redis_port,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            logger.log_error_with_context(
                "Redis health check failed",
                error=e,
                context={
                    "service": "redis",
                    "host": settings.redis_host,
                    "port": settings.redis_port
                }
            )
            return {
                "status": "unhealthy",
                "service": "redis",
                "error": str(e),
                "host": settings.redis_host,
                "port": settings.redis_port,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def check_rabbitmq(self) -> dict[str, Any]:
        """Check RabbitMQ connectivity."""
        try:
            # Create RabbitMQ broker
            broker = RabbitBroker(settings.rabbitmq_connection_string)

            # Test connection
            await broker.connect()
            await broker.close()

            return {
                "status": "healthy",
                "service": "rabbitmq",
                "host": settings.rabbitmq_host,
                "port": settings.rabbitmq_port,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            logger.log_error_with_context(
                "RabbitMQ health check failed",
                error=e,
                context={
                    "service": "rabbitmq",
                    "host": settings.rabbitmq_host,
                    "port": settings.rabbitmq_port
                }
            )
            return {
                "status": "unhealthy",
                "service": "rabbitmq",
                "error": str(e),
                "host": settings.rabbitmq_host,
                "port": settings.rabbitmq_port,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def check_keycloak(self) -> dict[str, Any]:
        """Check Keycloak connectivity."""
        return await keycloak_service.health_check()

    async def check_seq(self) -> dict[str, Any]:
        """Check Seq logging connectivity."""
        try:
            import httpx

            # Test Seq API health endpoint
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.seq_url}/health")
                response.raise_for_status()

            return {
                "status": "healthy",
                "service": "seq",
                "url": settings.seq_url,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            logger.log_error_with_context(
                "Seq health check failed",
                error=e,
                context={"service": "seq", "url": settings.seq_url}
            )
            return {
                "status": "unhealthy",
                "service": "seq",
                "error": str(e),
                "url": settings.seq_url,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def check_all_services(self) -> dict[str, Any]:
        """Check health of all services."""
        try:
            # Run all health checks concurrently
            results = await asyncio.gather(
                self.check_database(),
                self.check_redis(),
                self.check_rabbitmq(),
                self.check_keycloak(),
                self.check_seq(),
                return_exceptions=True,
            )

            # Process results
            services = {}
            overall_status = "healthy"

            for result in results:
                if isinstance(result, Exception):
                    services["error"] = {
                        "status": "unhealthy",
                        "error": str(result),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    overall_status = "unhealthy"
                elif isinstance(result, dict):
                    service_name = result.get("service", "unknown")
                    services[service_name] = result
                    if result.get("status") == "unhealthy":
                        overall_status = "unhealthy"
                else:
                    services["unknown"] = {
                        "status": "unhealthy",
                        "error": f"Unexpected result type: {type(result)}",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    overall_status = "unhealthy"

            return {
                "status": overall_status,
                "timestamp": datetime.now(UTC).isoformat(),
                "version": settings.version,
                "services": services,
            }
        except Exception as e:
            logger.log_error_with_context(
                "Health check failed",
                error=e
            )
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
                "version": settings.version,
            }


# Global health service instance
health_service = HealthService()
