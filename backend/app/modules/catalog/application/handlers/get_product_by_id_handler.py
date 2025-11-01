"""GetProductByIdHandler with 1-1 parity to .NET implementation."""

from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.application.features.product.queries.get_product_by_id.query import (
    GetProductByIdQuery,
    GetProductByIdResult,
)
from app.modules.catalog.contracts.product.dtos import ProductDto
from app.modules.catalog.domain.exceptions import ProductNotFoundError
from app.modules.catalog.infrastructure.cache_service import (
    CatalogCacheService,
    RedisCacheService,
)
from app.modules.catalog.infrastructure.persistence.repositories.product_repository import (
    ProductRepositoryImpl as ProductRepository,
)

logger = BaseLogger(__name__)


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
            # Convert SKU value object to string
            sku_str = str(product.sku) if product.sku else ""

            # Convert Money value object to float and get currency
            price_float = float(product.price.amount) if product.price else 0.0
            currency_str = product.price.currency if product.price else "USD"

            # Convert datetime fields to ISO format strings
            created_at_str = (
                product.created_at.isoformat() if product.created_at else ""
            )
            updated_at_str = (
                product.last_modified.isoformat() if product.last_modified else ""
            )

            # Handle image_file: convert empty strings to None
            image_file = (
                product.image_file.strip()
                if product.image_file and product.image_file.strip()
                else None
            )

            product_dto = ProductDto(
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

            # Cache the product
            await self.cache_service.set_product(
                product.id,
                product_dto.model_dump(),
                ttl=3600,  # 1 hour TTL
            )

            return GetProductByIdResult(product=product_dto)
