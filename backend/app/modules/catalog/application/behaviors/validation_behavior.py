"""Validation behavior for mediator pipeline."""

import logging
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from app.core.mediator.behaviors import IPipelineBehavior
from app.core.mediator.mediator import IRequest

logger = logging.getLogger(__name__)


class ValidationBehavior(IPipelineBehavior[IRequest, Any]):
    """Validation behavior for mediator pipeline."""

    async def handle(self, request: IRequest, next_handler: Callable[[], Any]) -> Any:
        """
        Handle request with validation.

        Args:
            request: The request to validate and handle
            next_handler: Next handler in the pipeline

        Returns:
            Result from the next handler

        Raises:
            ValidationError: If request validation fails
        """
        request_type = type(request).__name__
        logger.debug(f"Validating {request_type}")

        try:
            # Pydantic models are automatically validated on instantiation
            # This behavior can be extended for custom validation logic
            if hasattr(request, "model_validate"):
                # Additional validation if needed
                pass

            logger.debug(f"Validation passed for {request_type}")
            return await next_handler()

        except ValidationError as e:
            logger.error(f"Validation failed for {request_type}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during validation of {request_type}: {e}")
            raise
