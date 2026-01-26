"""Ordering module health check endpoint."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/ordering", tags=["ordering-health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> JSONResponse:
    """
    Health check endpoint for ordering module.

    Returns:
        JSON response with health status
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "module": "ordering"},
    )
