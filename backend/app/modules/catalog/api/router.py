"""Catalog module router."""
from typing import Any
from fastapi import APIRouter

from app.modules.catalog.api.endpoints import products

# Create the main catalog router
router = APIRouter()


# Add a simple test endpoint
@router.get("/test")
async def test_catalog() -> dict[str, str]:
    """Test endpoint to verify catalog router is working."""
    return {"message": "Catalog router is working!"}


# Add a simple RBAC test endpoint
@router.get("/rbac-test")
async def test_rbac() -> dict[str, str]:
    """Test endpoint to verify RBAC is working."""
    return {
        "message": "RBAC test endpoint - UPDATED",
        "description": "This endpoint tests RBAC functionality",
        "status": "working",
    }


# Include product endpoints
router.include_router(products.router)
