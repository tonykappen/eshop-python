"""Authorization behavior - enforces authorization rules before handlers execute."""

from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.behaviors import IPipelineBehavior

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class AuthorizationBehavior(IPipelineBehavior[TRequest, TResponse]):
    """Authorization behavior - enforces authorization rules before handlers execute."""

    def __init__(self) -> None:
        self.logger = BaseLogger(__name__)

    async def handle(
        self, request: TRequest, next_handler: Callable[[], Awaitable[TResponse]]
    ) -> TResponse:
        """
        Handle authorization - checks if the request is authorized before execution.
        
        Args:
            request: The request to authorize
            next_handler: Next handler in the pipeline
            
        Returns:
            Response from the next handler
            
        Raises:
            PermissionError: If the request is not authorized
        """
        # TODO: Implement authorization logic based on request type and user context
        # For now, this is a placeholder that allows all requests
        # In a full implementation, this would:
        # 1. Extract user context from request context
        # 2. Check if user has required permissions for the request type
        # 3. Raise PermissionError if not authorized
        
        request_type = type(request).__name__
        
        # Log authorization check (even if not enforcing yet)
        self.logger.log_debug_with_context(
            "Authorization check",
            context={"request_type": request_type},
        )
        
        # For now, allow all requests
        # In production, implement proper authorization checks here
        result = await next_handler()
        return result











