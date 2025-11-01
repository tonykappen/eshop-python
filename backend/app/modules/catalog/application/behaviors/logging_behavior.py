"""Logging behavior for mediator pipeline."""

import logging
from collections.abc import Callable
from typing import Any

from app.core.mediator.behaviors import IPipelineBehavior
from app.core.mediator.mediator import IRequest

logger = logging.getLogger(__name__)


class LoggingBehavior(IPipelineBehavior[IRequest, Any]):
    """Logging behavior for mediator pipeline."""

    async def handle(self, request: IRequest, next_handler: Callable[[], Any]) -> Any:
        """
        Handle request with logging.

        Args:
            request: The request to handle
            next_handler: Next handler in the pipeline

        Returns:
            Result from the next handler
        """
        request_type = type(request).__name__
        logger.info(f"Handling {request_type}: {request}")

        try:
            result = await next_handler()
            logger.info(f"Successfully handled {request_type}")
            return result
        except Exception as e:
            logger.error(f"Error handling {request_type}: {e}")
            raise
