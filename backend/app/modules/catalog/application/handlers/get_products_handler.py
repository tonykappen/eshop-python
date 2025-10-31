"""GetProductsHandler for listing products with pagination and filtering."""

import asyncio
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.contracts.cqrs import IQuery
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.core.pagination.models import PaginatedResult
from app.modules.catalog.contracts.product.dtos import ProductDto
from app.modules.catalog.domain.product.models.product import Product
from app.modules.catalog.infrastructure.persistence.repositories.product_repository_legacy import ProductRepository
from app.modules.catalog.infrastructure.cache_service import CatalogCacheService, RedisCacheService
from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class GetProductsQuery(IQuery[PaginatedResult[ProductDto]]):
    """Query to get products with optional filtering and pagination."""

    page: int = 1
    page_size: int = 10
    category_id: UUID | None = None
    search_term: str | None = None


class GetProductsHandler(
    IRequestHandler[GetProductsQuery, PaginatedResult[ProductDto]]
):
    """Handler for GetProductsQuery - provides paginated product listing."""

    def __init__(self) -> None:
        """Initialize handler."""
        self.cache_service = CatalogCacheService(RedisCacheService())

    async def handle(
        self, query: GetProductsQuery, cancellation_token: CancellationToken
    ) -> PaginatedResult[ProductDto]:
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

        # Try to get from cache first
        filters = self._build_filters(query)
        cached_result = await self.cache_service.get_products_list(
            query.page, query.page_size, filters
        )
        
        if cached_result:
            logger.log_debug_with_context(
                f"Returning cached products list for page {query.page}",
                page=query.page,
                page_size=query.page_size,
            )
            return PaginatedResult(**cached_result)

        # Cache miss - fetch from database
        logger.log_debug_with_context(
            f"Cache miss for products list, fetching from database",
            page=query.page,
            page_size=query.page_size,
        )

        # Use real database repository
        async with AsyncSessionLocal() as session:
            repository = ProductRepository(session)
            
            # Get products based on filters
            if query.search_term:
                products, total_count = await repository.search(
                    query.search_term, query.page, query.page_size
                )
            elif query.category_id:
                # For now, we'll use category name instead of ID
                # In a real implementation, you'd have a category lookup
                products, total_count = await repository.get_by_category(
                    str(query.category_id), query.page, query.page_size
                )
            else:
                products, total_count = await repository.get_all(
                    query.page, query.page_size
                )
            
            # Convert to DTOs
            product_dtos = [self._map_to_dto(product) for product in products]
            
            total_pages = (total_count + query.page_size - 1) // query.page_size
            result = PaginatedResult(
                items=product_dtos,
                total=total_count,
                page=query.page,
                size=query.page_size,
                pages=total_pages,
            )
            
            # Cache the result
            await self.cache_service.set_products_list(
                query.page, query.page_size, result.model_dump(), filters, ttl=1800  # 30 minutes
            )
            
            return result



    def _build_filters(self, query: GetProductsQuery) -> dict | None:
        """Build filters dictionary for cache key generation."""
        filters = {}
        if query.search_term:
            filters["search"] = query.search_term
        if query.category_id:
            filters["category"] = str(query.category_id)
        return filters if filters else None

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
