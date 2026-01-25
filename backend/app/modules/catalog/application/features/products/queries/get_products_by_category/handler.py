"""GetProductsByCategoryHandler - Category-filter handler for products."""

import logging
from decimal import Decimal
from typing import Any

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.core.database.session import AsyncSessionLocal
from app.modules.catalog.application.public_interface.dto.product import ProductDto
from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import (
    SqlProductRepository as ProductRepository,
)
from .query import GetProductsByCategoryQuery, GetProductsByCategoryResult

logger = logging.getLogger(__name__)


class GetProductsByCategoryHandler(
    IRequestHandler[GetProductsByCategoryQuery, GetProductsByCategoryResult]
):
    """Category-filter handler for GetProductsByCategoryQuery."""

    def __init__(self) -> None:
        """Initialize handler."""
        pass

    async def handle(
        self, query: GetProductsByCategoryQuery, cancellation_token: CancellationToken
    ) -> GetProductsByCategoryResult:
        """
        Handle the query to get products filtered by category with pagination.

        Args:
            query: The query containing category filter and pagination parameters
            cancellation_token: Cancellation token for async operations

        Returns:
            GetProductsByCategoryResult containing paginated products filtered by category
        """
        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Use real database repository
        async with AsyncSessionLocal() as session:
            repository = ProductRepository(session)
            
            logger.info(
                f"GetProductsByCategoryHandler: category={query.category}, "
                f"page={query.page}, page_size={query.page_size}"
            )
            
            # Get products by category
            result = await repository.get_by_category(
                query.category, query.page, query.page_size
            )
            
            # Handle both tuple and list return types
            if isinstance(result, tuple):
                products, total_count = result
            else:
                products = result
                total_count = len(products)
            
            logger.info(
                f"Repository returned {len(products)} products for category '{query.category}', "
                f"total_count={total_count}"
            )
            
            # Convert to DTOs
            product_dtos = [self._map_to_dto(product) for product in products]
            
            logger.info(f"Converted to {len(product_dtos)} DTOs")
            
            # Calculate total pages
            total_pages = (total_count + query.page_size - 1) // query.page_size if total_count > 0 else 0
            
            return GetProductsByCategoryResult(
                items=product_dtos,
                total=total_count,
                page=query.page,
                size=query.page_size,
                pages=total_pages,
                category=query.category,
            )

    def _map_to_dto(self, product: Product) -> ProductDto:
        """
        Map product entity to DTO.
        
        Args:
            product: Product domain entity
            
        Returns:
            ProductDto instance
        """
        # Convert SKU value object to string
        sku_str = str(product.sku) if product.sku else ""
        
        # Convert Money value object to float and get currency
        price_float = float(product.price.amount) if product.price else 0.0
        currency_str = product.price.currency if product.price else "USD"
        
        # Convert datetime fields to ISO format strings
        created_at_str = product.created_at.isoformat() if product.created_at else ""
        updated_at_str = product.last_modified.isoformat() if product.last_modified else ""
        
        # Handle image_file: convert empty strings to None
        image_file = (
            product.image_file.strip() 
            if product.image_file and product.image_file.strip() 
            else None
        )
        
        return ProductDto(
            id=product.id,
            name=product.name,
            sku=sku_str,
            category=product.category,
            description=product.description,
            image_file=image_file,
            price=price_float,
            currency=currency_str,
            version=product.version,
            created_at=created_at_str,
            updated_at=updated_at_str,
        )
