"""Health check endpoints for catalog module."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.presentation.deps import get_catalog_session
from app.modules.catalog.infrastructure.persistence.db_context import get_engine

logger = logging.getLogger(__name__)

# Create router for health endpoints
health_router = APIRouter()


@health_router.get("/healthz")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns:
        Dict with health status
    """
    return {
        "status": "healthy",
        "service": "catalog",
        "version": "1.0.0"
    }


@health_router.get("/ready")
async def readiness_check(
    session: AsyncSession = Depends(get_catalog_session)
) -> Dict[str, Any]:
    """
    Readiness check endpoint.
    
    Args:
        session: Database session
        
    Returns:
        Dict with readiness status
    """
    try:
        # Check database connectivity
        await session.execute(text("SELECT 1"))
        
        # Check if required tables exist
        tables_check = await _check_required_tables(session)
        
        return {
            "status": "ready",
            "service": "catalog",
            "checks": {
                "database": "healthy",
                "tables": tables_check
            }
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


@health_router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    
    Returns:
        Dict with liveness status
    """
    return {
        "status": "alive",
        "service": "catalog"
    }


async def _check_required_tables(session: AsyncSession) -> Dict[str, str]:
    """
    Check if required tables exist.
    
    Args:
        session: Database session
        
    Returns:
        Dict with table check results
    """
    required_tables = [
        "catalog.products",
        "catalog.categories", 
        "catalog.inventory_items",
        "catalog.outbox"
    ]
    
    results = {}
    
    for table in required_tables:
        try:
            await session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
            results[table] = "exists"
        except Exception as e:
            logger.warning(f"Table {table} check failed: {e}")
            results[table] = "missing"
    
    return results


@health_router.get("/health/detailed")
async def detailed_health_check(
    session: AsyncSession = Depends(get_catalog_session)
) -> Dict[str, Any]:
    """
    Detailed health check endpoint.
    
    Args:
        session: Database session
        
    Returns:
        Dict with detailed health information
    """
    try:
        # Database health
        db_health = await _check_database_health(session)
        
        # Table health
        table_health = await _check_required_tables(session)
        
        # Service health
        service_health = {
            "status": "healthy",
            "uptime": "unknown",  # Would be calculated in real implementation
            "version": "1.0.0"
        }
        
        # Overall health
        overall_healthy = (
            db_health["status"] == "healthy" and
            all(status == "exists" for status in table_health.values())
        )
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "catalog",
            "checks": {
                "database": db_health,
                "tables": table_health,
                "service": service_health
            },
            "timestamp": "2024-01-15T10:30:00Z"  # Would be current timestamp
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "catalog",
            "error": str(e),
            "timestamp": "2024-01-15T10:30:00Z"
        }


async def _check_database_health(session: AsyncSession) -> Dict[str, Any]:
    """
    Check database health.
    
    Args:
        session: Database session
        
    Returns:
        Dict with database health information
    """
    try:
        # Test basic connectivity
        await session.execute(text("SELECT 1"))
        
        # Test schema existence
        schema_result = await session.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'catalog'")
        )
        schema_exists = schema_result.fetchone() is not None
        
        return {
            "status": "healthy" if schema_exists else "unhealthy",
            "connectivity": "ok",
            "schema": "exists" if schema_exists else "missing"
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connectivity": "failed",
            "error": str(e)
        }


