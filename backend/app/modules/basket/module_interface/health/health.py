"""Basket module health check endpoints."""

from app.modules.basket.module_interface.di.basket.basket_providers import \
    get_basket_session
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/health", tags=["basket-health"])


@router.get("/")
async def basket_health(
    session: AsyncSession = Depends(get_basket_session),
) -> dict[str, str]:
    """
    Basket module health check.

    Returns:
        Health status
    """
    try:
        # Simple health check - try to execute a query
        await session.execute(text("SELECT 1"))
        return {"status": "healthy", "module": "basket"}
    except Exception as e:
        return {"status": "unhealthy", "module": "basket", "error": str(e)}


@router.get("/ready")
async def basket_ready(
    session: AsyncSession = Depends(get_basket_session),
) -> dict[str, str]:
    """
    Basket module readiness check.

    Returns:
        Readiness status
    """
    try:
        # Check database connectivity
        await session.execute(text("SELECT 1"))
        return {"status": "ready", "module": "basket"}
    except Exception as e:
        return {"status": "not_ready", "module": "basket", "error": str(e)}
