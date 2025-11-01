"""API versioning configuration for catalog module."""

import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)


class CatalogAPIVersioning:
    """API versioning configuration for catalog module."""

    # API base prefix
    API_BASE_PREFIX = "/api/v1/catalog"

    # OpenAPI tags
    OPENAPI_TAGS = [
        {
            "name": "catalog",
            "description": "Catalog operations for products, categories, and inventory",
        },
        {
            "name": "products",
            "description": "Product management operations",
        },
        {
            "name": "categories",
            "description": "Category management operations",
        },
        {
            "name": "inventory",
            "description": "Inventory management operations",
        },
        {
            "name": "health",
            "description": "Health check endpoints",
        },
    ]

    # API metadata
    API_METADATA = {
        "title": "Catalog API",
        "description": "API for managing catalog data including products, categories, and inventory",
        "version": "1.0.0",
        "contact": {
            "name": "Catalog Team",
            "email": "catalog@eshop.com",
        },
        "license_info": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    }

    @staticmethod
    def create_catalog_router() -> APIRouter:
        """
        Create the main catalog router with versioning.

        Returns:
            APIRouter: Configured router
        """
        router = APIRouter(
            prefix=CatalogAPIVersioning.API_BASE_PREFIX,
            tags=["catalog"],
            responses={
                404: {"description": "Not found"},
                422: {"description": "Validation error"},
                500: {"description": "Internal server error"},
            },
        )

        logger.info(
            f"Created catalog router with prefix: {CatalogAPIVersioning.API_BASE_PREFIX}"
        )
        return router

    @staticmethod
    def create_products_router() -> APIRouter:
        """
        Create the products router.

        Returns:
            APIRouter: Configured router
        """
        router = APIRouter(
            prefix="/products",
            tags=["products"],
            responses={
                404: {"description": "Product not found"},
                409: {"description": "Product already exists"},
                422: {"description": "Validation error"},
            },
        )

        return router

    @staticmethod
    def create_categories_router() -> APIRouter:
        """
        Create the categories router.

        Returns:
            APIRouter: Configured router
        """
        router = APIRouter(
            prefix="/categories",
            tags=["categories"],
            responses={
                404: {"description": "Category not found"},
                409: {"description": "Category already exists"},
                422: {"description": "Validation error"},
            },
        )

        return router

    @staticmethod
    def create_inventory_router() -> APIRouter:
        """
        Create the inventory router.

        Returns:
            APIRouter: Configured router
        """
        router = APIRouter(
            prefix="/inventory",
            tags=["inventory"],
            responses={
                404: {"description": "Inventory item not found"},
                422: {"description": "Validation error"},
            },
        )

        return router

    @staticmethod
    def create_health_router() -> APIRouter:
        """
        Create the health router.

        Returns:
            APIRouter: Configured router
        """
        router = APIRouter(
            prefix="/health",
            tags=["health"],
            responses={
                503: {"description": "Service unavailable"},
            },
        )

        return router

    @staticmethod
    def get_api_info() -> dict[str, Any]:
        """
        Get API information.

        Returns:
            Dict with API information
        """
        return {
            "api_prefix": CatalogAPIVersioning.API_BASE_PREFIX,
            "version": "1.0.0",
            "tags": CatalogAPIVersioning.OPENAPI_TAGS,
            "metadata": CatalogAPIVersioning.API_METADATA,
        }

    @staticmethod
    def setup_openapi_tags(app) -> None:
        """
        Set up OpenAPI tags for the FastAPI app.

        Args:
            app: FastAPI application instance
        """
        if hasattr(app, "openapi_tags"):
            app.openapi_tags = CatalogAPIVersioning.OPENAPI_TAGS

        logger.info("Set up OpenAPI tags for catalog module")

    @staticmethod
    def setup_api_metadata(app) -> None:
        """
        Set up API metadata for the FastAPI app.

        Args:
            app: FastAPI application instance
        """
        # Update app metadata
        for key, value in CatalogAPIVersioning.API_METADATA.items():
            if hasattr(app, key):
                setattr(app, key, value)

        logger.info("Set up API metadata for catalog module")
