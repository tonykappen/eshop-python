"""Catalog module router."""

from fastapi import APIRouter

# Create the main catalog router
router = APIRouter()

# Add a simple test endpoint
@router.get("/test")
async def test_catalog():
    """Test endpoint to verify catalog router is working."""
    return {"message": "Catalog router is working!"}

# Add a simple RBAC test endpoint
@router.get("/rbac-test")
async def test_rbac():
    """Test endpoint to verify RBAC is working."""
    return {
        "message": "RBAC test endpoint",
        "description": "This endpoint tests RBAC functionality",
        "status": "working"
    }

# Include product endpoints
from eshop.modules.catalog.api.endpoints import products
router.include_router(products.router, prefix="/catalog")
