"""Global health and ready endpoints."""

from fastapi import APIRouter

from app.core.health.health_endpoints import health_router as core_health_router

# Use the core health router
health_router = core_health_router

__all__ = ["health_router"]












