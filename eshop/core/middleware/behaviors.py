"""Middleware behavior classes with enhanced auto-logging."""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from eshop.core.logging.logger import AutoLogContext, get_logger


def logging_behavior(func: Callable[..., Any]) -> Callable[..., Any]:
    """Logging behavior decorator."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
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


def validation_behavior(func: Callable[..., Any]) -> Callable[..., Any]:
    """Validation behavior decorator."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
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

    def __init__(self) -> None:
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

    def __init__(self, event_publisher: Any) -> None:
        self.event_publisher = event_publisher
        self.logger = get_logger(__name__)

    async def dispatch_events(self, entity: Any) -> None:
        """Dispatch domain events from an entity."""
        if hasattr(entity, "domain_events") and entity.domain_events:
            async with AutoLogContext(
                self.logger,
                f"dispatching {len(entity.domain_events)} events from {type(entity).__name__}",
            ):
                for event in entity.domain_events:
                    self.logger.debug(f"Dispatching event: {type(event).__name__}")
                    await self.event_publisher.publish_domain_event(event)

                entity.clear_domain_events()


# Auto-logging decorators for various scenarios
def auto_log_async(operation_name: str | None = None) -> Callable[..., Any]:
    """Decorator for automatic async function logging."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(func.__module__)
            op_name = operation_name or func.__name__

            async with AutoLogContext(logger, op_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def auto_log_sync(operation_name: str | None = None) -> Callable[..., Any]:
    """Decorator for automatic sync function logging."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(func.__module__)
            op_name = operation_name or func.__name__
            start_time = time.time()

            logger.info(f"Starting {op_name}")

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Completed {op_name}", execution_time=execution_time)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Failed {op_name}: {e}",
                    execution_time=execution_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise

        return wrapper

    return decorator


def auto_log_database_operation(
    operation_name: str | None = None,
) -> Callable[..., Any]:
    """Decorator specifically for database operations with enhanced logging."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(func.__module__)
            op_name = operation_name or f"database.{func.__name__}"

            async with AutoLogContext(logger, op_name):
                # Log SQL operations, transaction info, etc.
                if hasattr(args[0], "__class__"):
                    logger.debug(f"Database operation on: {args[0].__class__.__name__}")
                return await func(*args, **kwargs)

        return wrapper

    return decorator


class PerformanceLoggingMixin:
    """Mixin to add performance logging to any class."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)

    def log_performance(self, operation: str, duration: float, **context: Any) -> None:
        """Log performance metrics."""
        self.logger.info(
            f"Performance: {operation}",
            duration_ms=round(duration * 1000, 2),
            **context,
        )

        # Log warning for slow operations
        if duration > 1.0:  # More than 1 second
            self.logger.warning(
                f"Slow operation detected: {operation}",
                duration_ms=round(duration * 1000, 2),
                **context,
            )
