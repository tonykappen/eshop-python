"""GetProductsHandler for listing products with pagination and filtering."""

import asyncio
from decimal import Decimal
from typing import Any
from uuid import UUID
import logging

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.application.public_interface.dto.product import ProductDto
from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import SqlProductRepository as ProductRepository
from app.core.database.session import AsyncSessionLocal
from .query import GetProductsQuery, GetProductsResult

logger = logging.getLogger(__name__)


class GetProductsHandler(
    IRequestHandler[GetProductsQuery, GetProductsResult]
):
    """Handler for GetProductsQuery - provides paginated product listing."""

    def __init__(self) -> None:
        """Initialize handler."""
        pass

    async def handle(
        self, query: GetProductsQuery, cancellation_token: CancellationToken
    ) -> GetProductsResult:
        """
        Handle the query to get products with pagination and filtering.

        Args:
            query: The query containing pagination and filter parameters
            cancellation_token: Cancellation token for async operations

        Returns:
            PaginatedResult containing paginated products
        """
        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Use real database repository
        async with AsyncSessionLocal() as session:
            repository = ProductRepository(session)
            
            logger.info(f"GetProductsHandler: page={query.page}, page_size={query.page_size}, search_term={query.search_term}, category_id={query.category_id}")
            
            # Get products based on filters
            if query.search_term:
                logger.info(f"Using search with term: {query.search_term}")
                products, total_count = await repository.search(
                    query.search_term, query.page, query.page_size
                )
            elif query.category_id:
                logger.info(f"Using category filter: {query.category_id}")
                # For now, we'll use category name instead of ID
                # In a real implementation, you'd have a category lookup
                products, total_count = await repository.get_by_category(
                    str(query.category_id), query.page, query.page_size
                )
            else:
                logger.info("Using get_all (no filters)")
                products, total_count = await repository.get_all(
                    query.page, query.page_size
                )
            
            logger.info(f"Repository returned {len(products)} products, total_count={total_count}")
            
            # Convert to DTOs
            product_dtos = [self._map_to_dto(product) for product in products]
            
            logger.info(f"Converted to {len(product_dtos)} DTOs")
            
            total_pages = (total_count + query.page_size - 1) // query.page_size
            return GetProductsResult(
                items=product_dtos,
                total=total_count,
                page=query.page,
                size=query.page_size,
                pages=total_pages,
            )



    def _map_to_dto(self, product: Product) -> ProductDto:
        """Map product entity to DTO."""
        # Convert SKU value object to string
        sku_str = str(product.sku) if product.sku else ""
        
        # Convert Money value object to float and get currency
        price_float = float(product.price.amount) if product.price else 0.0
        currency_str = product.price.currency if product.price else "USD"
        
        # Convert datetime fields to ISO format strings
        created_at_str = product.created_at.isoformat() if product.created_at else ""
        updated_at_str = product.last_modified.isoformat() if product.last_modified else ""
        
        # Handle image_file: convert empty strings to None
        image_file = product.image_file.strip() if product.image_file and product.image_file.strip() else None
        
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
