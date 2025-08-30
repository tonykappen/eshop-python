"""Catalog module router."""

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


# Add a test products endpoint that doesn't require authentication
@router.get("/products-test")
async def test_products() -> dict[str, Any]:
    """Test endpoint to verify products functionality without authentication."""
    return {
        "message": "Products API is working!",
        "description": "This endpoint tests products functionality without RBAC",
        "status": "working",
        "note": "This is a test endpoint - real products endpoints require authentication",
        "available_endpoints": [
            "GET /api/v1/products/ - Get all products (requires auth)",
            "GET /api/v1/products/{id} - Get product by ID (requires auth)",
            "POST /api/v1/products/ - Create product (requires auth)"
        ]
    }


# Include product endpoints
router.include_router(products.router)
