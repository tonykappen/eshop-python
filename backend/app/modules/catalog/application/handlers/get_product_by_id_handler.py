"""GetProductByIdHandler with 1-1 parity to .NET implementation."""

import asyncio
from typing import Any
from uuid import UUID

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.contracts.products.dtos import ProductDto
from app.modules.catalog.contracts.products.features.get_product_by_id import (
    GetProductByIdQuery,
    GetProductByIdResult,
)
from app.modules.catalog.domain.exceptions import ProductNotFoundError
from app.modules.catalog.infrastructure.product_repository import ProductRepository
from app.modules.catalog.infrastructure.cache_service import CatalogCacheService, RedisCacheService
from app.core.database.session import AsyncSessionLocal
from app.core.logging.logger import get_logger

logger = get_logger(__name__)


class GetProductByIdHandler(IRequestHandler[GetProductByIdQuery, GetProductByIdResult]):
    """Handler for GetProductByIdQuery - matches .NET GetProductByIdHandler."""

    def __init__(self) -> None:
        """Initialize handler."""
        self.cache_service = CatalogCacheService(RedisCacheService())

    async def handle(
        self, query: GetProductByIdQuery, cancellation_token: CancellationToken
    ) -> GetProductByIdResult:
        """
        Handle the query - matches .NET Handle(GetProductByIdQuery query, CancellationToken cancellationToken).

        Args:
            query: The query to handle

        Returns:
            GetProductByIdResult containing the product

        Raises:
            ProductNotFoundException: If product is not found
        """
        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Try to get from cache first
        cached_product = await self.cache_service.get_product(query.id)
        
        if cached_product:
            logger.log_debug_with_context(
                f"Returning cached product {query.id}",
                product_id=str(query.id),
            )
            product_dto = ProductDto(**cached_product)
            return GetProductByIdResult(product=product_dto)

        # Cache miss - fetch from database
        logger.log_debug_with_context(
            f"Cache miss for product {query.id}, fetching from database",
            product_id=str(query.id),
        )

        # Use real database repository
        async with AsyncSessionLocal() as session:
            repository = ProductRepository(session)
            product = await repository.get_by_id(query.id)

            if product is None:
                raise ProductNotFoundError(query.id)

            # Mapping product entity to ProductDto
            product_dto = ProductDto(
                id=product.id,
                name=product.name,
                category=product.category,
                description=product.description,
                picture_url=product.image_file,  # Map image_file to picture_url
                price=product.price,
            )

            # Cache the product
            await self.cache_service.set_product(
                product.id,
                product_dto.model_dump(),
                ttl=3600  # 1 hour TTL
            )

            return GetProductByIdResult(product=product_dto)

