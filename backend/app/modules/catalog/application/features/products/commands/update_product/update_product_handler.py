"""UpdateProductHandler with 1-1 parity to .NET implementation."""

from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.exceptions.product import (
    ProductNotFoundError,
    ProductUpdateError,
    ProductValidationError,
)
from app.modules.catalog.application.services.catalog_cache_service import (
    CatalogCacheService,
    RedisCacheService,
)
from app.modules.catalog.infrastructure.persistence.repositories.products.redis.cached_product_repository import (
    CachedProductRepository,
)
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import (
    SqlProductRepository,
)

from .update_product_command import UpdateProductCommand, UpdateProductResult

logger = BaseLogger(__name__)


class UpdateProductCommandValidator:
    """Validator for UpdateProductCommand - matches .NET UpdateProductCommandValidator."""

    def validate(self, command: UpdateProductCommand) -> list[str]:
        """
        Validate the update product command.

        Args:
            command: The command to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not command.id:
            errors.append("Id is required")

        if not command.name or not command.name.strip():
            errors.append("Name is required")

        if command.price <= 0:
            errors.append("Price must be greater than 0")

        if not command.description or not command.description.strip():
            errors.append("Description is required")

        # picture_url is now optional, so no validation needed

        if not command.category:
            errors.append("At least one category is required")

        return errors


class UpdateProductHandler(IRequestHandler[UpdateProductCommand, UpdateProductResult]):
    """Handler for UpdateProductCommand - matches .NET UpdateProductHandler."""

    def __init__(self) -> None:
        """Initialize handler."""
        pass

    async def handle(
        self, command: UpdateProductCommand, cancellation_token: CancellationToken
    ) -> UpdateProductResult:
        """
        Handle the command - matches .NET Handle(UpdateProductCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            UpdateProductResult indicating success

        Raises:
            ProductNotFoundError: If product with given ID is not found
            ProductUpdateError: If update operation fails
        """
        # Validate command first
        validator = UpdateProductCommandValidator()
        errors = validator.validate(command)
        if errors:
            raise ProductValidationError(
                f"Command validation failed: {', '.join(errors)}"
            )

        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Use Unit of Work to ensure interceptors are called
        from app.modules.catalog.infrastructure.persistence.unit_of_work import (
            SqlCatalogUnitOfWork,
        )

        async with AsyncSessionLocal() as session:
            uow = SqlCatalogUnitOfWork(session)
            repository = uow.products

            # Read directly from DB (bypass cache) to get the latest version
            # for optimistic locking. Using cached data here causes
            # OptimisticLockException when the cached version is stale.
            sql_repo = SqlProductRepository(session)
            product = await sql_repo.get_by_id(command.id)
            if product is None:
                raise ProductNotFoundError(command.id)

            try:
                # Store old price for comparison
                old_price = product.price
                
                # Update product with new values (raises domain events)
                # This MUST happen before repository.update() to preserve domain events
                self._update_product_with_new_values(product, command)
                
                # Log if price changed and domain event was raised
                domain_event_count = len(product.domain_events) if hasattr(product, 'domain_events') else 0
                if old_price != product.price:
                    logger.log_with_context(
                        "Price changed",
                        context={
                            "product_id": str(command.id),
                            "old_price": str(old_price),
                            "new_price": str(product.price),
                            "domain_event_count": domain_event_count
                        }
                    )
                else:
                    logger.log_with_context(
                        "Price unchanged",
                        context={
                            "product_id": str(command.id),
                            "price": str(product.price),
                            "domain_event_count": domain_event_count
                        }
                    )

                uow.track(product)

                updated_product = await repository.update(product)

                if updated_product and hasattr(product, "domain_events") and product.domain_events:
                    if hasattr(updated_product, "domain_events"):
                        from copy import deepcopy
                        updated_product.domain_events = []
                        for event in product.domain_events:
                            event_copy = deepcopy(event)
                            if hasattr(event_copy, "product"):
                                event_copy.product = updated_product
                            updated_product.domain_events.append(event_copy)
                    uow.track(updated_product)

                # Commit via UoW (calls interceptors)
                await uow.commit()

                # Invalidate caches so list/detail APIs return fresh data
                cache_service = CatalogCacheService(RedisCacheService())
                await cache_service.invalidate_product(command.id)

                return UpdateProductResult(is_success=True)
            except Exception as e:
                await uow.rollback()
                raise ProductUpdateError(
                    message="Failed to update product in database", details=str(e)
                ) from e

    def _update_product_with_new_values(
        self, product: Product, command: UpdateProductCommand
    ) -> None:
        """
        Update product with new values - matches .NET UpdateProductWithNewValues method.

        Args:
            product: Product entity to update
            command: Update command with new values
        """
        try:
            from decimal import Decimal

            from app.modules.catalog.domain.value_objects import Money

            # Convert float price to Money value object
            # Use existing currency from product or default to USD
            currency = product.price.currency if product.price else "USD"
            price_money = Money(amount=Decimal(str(command.price)), currency=currency)

            # Use provided picture_url if it exists, otherwise keep existing image_file
            # Handle empty string as valid (optional field)
            if command.picture_url is not None:
                image_file = (
                    command.picture_url.strip() if command.picture_url.strip() else ""
                )
            else:
                image_file = product.image_file or ""

            product.update(
                name=command.name,
                category=command.category,
                description=command.description,
                image_file=image_file,  # Map picture_url to image_file for domain model
                price=price_money,
            )
        except Exception as e:
            raise ProductValidationError(f"Failed to update product: {str(e)}") from e
