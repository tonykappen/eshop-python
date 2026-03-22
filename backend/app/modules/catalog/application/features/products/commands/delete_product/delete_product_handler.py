"""DeleteProductHandler with 1-1 parity to .NET implementation."""

from collections.abc import Callable
from typing import Any

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.domain.exceptions.product import (
    ProductDeleteError,
    ProductNotFoundError,
    ProductValidationError,
)

from .delete_product_command import DeleteProductCommand, DeleteProductResult

logger = BaseLogger(__name__)


class DeleteProductCommandValidator:
    """Validator for DeleteProductCommand."""

    def validate(self, command: DeleteProductCommand) -> list[str]:
        errors: list[str] = []
        if not command.product_id:
            errors.append("Product Id is required")
        return errors


class DeleteProductHandler(IRequestHandler[DeleteProductCommand, DeleteProductResult]):
    """Handler for DeleteProductCommand."""

    def __init__(self, uow_factory: Callable[[], Any] | None = None) -> None:
        self._uow_factory = uow_factory

    async def handle(
        self, command: DeleteProductCommand, cancellation_token: CancellationToken
    ) -> DeleteProductResult:
        validator = DeleteProductCommandValidator()
        errors = validator.validate(command)
        if errors:
            raise ProductValidationError(
                f"Command validation failed: {', '.join(errors)}"
            )

        cancellation_token.throw_if_cancellation_requested()

        if self._uow_factory is None:
            raise ProductDeleteError(
                message="Handler not properly configured: missing UoW factory"
            )

        async with self._uow_factory() as uow:
            product = await uow.products.get_by_id(command.product_id)
            if product is None:
                raise ProductNotFoundError(command.product_id)

            try:
                product.deactivate()
                uow.track(product)

                success = await uow.products.delete(
                    command.product_id,
                    deleted_by=command.deleted_by,
                    deletion_reason=command.deletion_reason,
                )

                if not success:
                    raise ProductDeleteError(
                        message="Failed to delete product from database"
                    )

                logger.log_with_context(
                    "Product soft-deleted successfully",
                    context={"product_id": str(command.product_id)},
                )
                return DeleteProductResult(is_success=True)
            except ProductDeleteError:
                raise
            except Exception as e:
                raise ProductDeleteError(
                    message="Failed to delete product from database", details=str(e)
                ) from e
