"""Authorization behavior for mediator pipeline."""

import logging
from collections.abc import Callable
from typing import Any

from app.core.mediator.behaviors import IPipelineBehavior
from app.core.mediator.mediator import IRequest

logger = logging.getLogger(__name__)


class AuthorizationBehavior(IPipelineBehavior[IRequest, Any]):
    """Authorization behavior for mediator pipeline."""

    async def handle(self, request: IRequest, next_handler: Callable[[], Any]) -> Any:
        """
        Handle request with authorization check.

        Args:
            request: The request to authorize
            next_handler: Next handler in the pipeline

        Returns:
            Result from the next handler

        Raises:
            PermissionError: If authorization fails
        """
        request_type = type(request).__name__
        logger.debug(f"Authorizing {request_type}")

        try:
            # Check if request has authorization requirements
            if (  # noqa: SIM102
                hasattr(request, "requires_authorization")
                and request.requires_authorization
            ):
                # Perform authorization check
                if not await self._check_authorization(request):
                    logger.warning(f"Authorization failed for {request_type}")
                    raise PermissionError(f"Not authorized to perform {request_type}")

            logger.debug(f"Authorization passed for {request_type}")
            return await next_handler()

        except PermissionError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during authorization of {request_type}: {e}"
            )
            raise

    async def _check_authorization(self, request: IRequest) -> bool:  # noqa: ARG002
        """
        Check if the request is authorized.

        Args:
            request: The request to check

        Returns:
            True if authorized, False otherwise
        """
        # This is a placeholder implementation
        # In a real application, this would check user permissions, roles, etc.

        # For now, allow all requests
        # You could implement role-based checks here:
        # - Check if user has required role
        # - Check if user owns the resource
        # - Check if user has permission for the operation

        return True
