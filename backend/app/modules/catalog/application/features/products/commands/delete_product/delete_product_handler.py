"""DeleteProductHandler with 1-1 parity to .NET implementation."""

from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.domain.exceptions.product import (
    ProductDeleteError,
    ProductNotFoundError,
)

from .delete_product_command import DeleteProductCommand, DeleteProductResult

logger = BaseLogger(__name__)


class DeleteProductCommandValidator:
    """Validator for DeleteProductCommand."""

    def validate(self, command: DeleteProductCommand) -> list[str]:
        errors = []
        if not command.product_id:
            errors.append("Product Id is required")
        return errors


class DeleteProductHandler(IRequestHandler[DeleteProductCommand, DeleteProductResult]):
    """Handler for DeleteProductCommand."""

    async def handle(
        self, command: DeleteProductCommand, cancellation_token: CancellationToken
    ) -> DeleteProductResult:
        validator = DeleteProductCommandValidator()
        errors = validator.validate(command)
        if errors:
            from app.modules.catalog.domain.exceptions.product import (
                ProductValidationError,
            )
            raise ProductValidationError(
                f"Command validation failed: {', '.join(errors)}"
            )

        cancellation_token.throw_if_cancellation_requested()

        from app.modules.catalog.infrastructure.persistence.unit_of_work import (
            SqlCatalogUnitOfWork,
        )

        async with AsyncSessionLocal() as session:
            uow = SqlCatalogUnitOfWork(session)
            repository = uow.products

            product = await repository.get_by_id(command.product_id)
            if product is None:
                raise ProductNotFoundError(command.product_id)

            try:
                product.deactivate()

                uow.track(product)

                success = await repository.delete(
                    command.product_id,
                    deleted_by=command.deleted_by,
                    deletion_reason=command.deletion_reason,
                )

                if not success:
                    raise ProductDeleteError(
                        message="Failed to delete product from database"
                    )

                await uow.commit()

                # Invalidate caches so list/detail APIs return fresh data
                from app.modules.catalog.application.services.catalog_cache_service import (
                    CatalogCacheService,
                    RedisCacheService,
                )
                cache_service = CatalogCacheService(RedisCacheService())
                await cache_service.invalidate_product(command.product_id)

                logger.log_with_context(
                    "Product soft-deleted successfully",
                    context={"product_id": str(command.product_id)},
                )
                return DeleteProductResult(is_success=True)
            except Exception as e:
                await uow.rollback()
                raise ProductDeleteError(
                    message="Failed to delete product from database", details=str(e)
                ) from e
