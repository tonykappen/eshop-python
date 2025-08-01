"""Middleware behavior classes."""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from eshop.core.logging.logger import get_logger


def logging_behavior(func: Callable) -> Callable:
    """Logging behavior decorator."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        logger = get_logger(func.__module__)

        start_time = time.time()
        logger.info(f"Starting {func.__name__}", extra={"function": func.__name__})

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(
                f"Completed {func.__name__}",
                extra={"function": func.__name__, "execution_time": execution_time},
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "error": str(e),
                },
            )
            raise

    return wrapper


def validation_behavior(func: Callable) -> Callable:
    """Validation behavior decorator."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        logger = get_logger(func.__module__)

        # Validate input parameters
        if hasattr(func, "__annotations__"):
            logger.debug(f"Validating input for {func.__name__}")
            # TODO: Add input validation logic

        result = await func(*args, **kwargs)

        # Validate output
        logger.debug(f"Validating output for {func.__name__}")
        # TODO: Add output validation logic

        return result

    return wrapper


class AuditableEntityInterceptor:
    """Interceptor for auditable entities."""

    def __init__(self):
        self.logger = get_logger(__name__)

    async def before_save(self, entity: Any) -> None:
        """Called before saving an entity."""
        self.logger.debug(f"Before save: {type(entity).__name__}")
        # TODO: Add audit logic

    async def after_save(self, entity: Any) -> None:
        """Called after saving an entity."""
        self.logger.debug(f"After save: {type(entity).__name__}")
        # TODO: Add audit logic


class DispatchDomainEventsInterceptor:
    """Interceptor for dispatching domain events."""

    def __init__(self, event_publisher):
        self.event_publisher = event_publisher
        self.logger = get_logger(__name__)

    async def dispatch_events(self, entity: Any) -> None:
        """Dispatch domain events from an entity."""
        if hasattr(entity, "domain_events") and entity.domain_events:
            self.logger.debug(
                f"Dispatching {len(entity.domain_events)} events from {type(entity).__name__}"
            )

            for event in entity.domain_events:
                await self.event_publisher.publish_domain_event(event)

            entity.clear_domain_events()
