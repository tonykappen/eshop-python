"""Product router - groups all product endpoints."""

# Import all product endpoint routers
from app.modules.catalog.presentation.endpoints.products.command.create_product.create_product_endpoint import \
    router as create_product_router
from app.modules.catalog.presentation.endpoints.products.command.delete_product.delete_product_endpoint import \
    router as delete_product_router
from app.modules.catalog.presentation.endpoints.products.command.update_product.update_product_endpoint import \
    router as update_product_router
from app.modules.catalog.presentation.endpoints.products.query.get_product_by_id.get_product_by_id_endpoint import \
    router as get_product_by_id_router
from app.modules.catalog.presentation.endpoints.products.query.get_products.get_products_endpoint import \
    router as get_products_router
from app.modules.catalog.presentation.endpoints.products.query.get_products_by_category.get_products_by_category_endpoint import \
    router as get_products_by_category_router
from fastapi import APIRouter

# Create the main product router
router = APIRouter(prefix="/products", tags=["products"])

# Include all product endpoint routers
router.include_router(create_product_router)
router.include_router(update_product_router)
router.include_router(delete_product_router)
router.include_router(get_product_by_id_router)
router.include_router(get_products_router)
router.include_router(get_products_by_category_router)
