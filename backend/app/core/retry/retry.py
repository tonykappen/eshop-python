"""Retry mechanisms using tenacity for handling transient failures."""

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class RetryConfig:
    """Configuration for retry mechanisms."""

    def __init__(
        self,
        max_attempts: int = 3,
        wait_time: float = 1.0,
        max_wait_time: float = 60.0,
        retry_exceptions: tuple = (Exception,),
        timeout: float | None = None,
    ):
        self.max_attempts = max_attempts
        self.wait_time = wait_time
        self.max_wait_time = max_wait_time
        self.retry_exceptions = retry_exceptions
        self.timeout = timeout


def retry_operation(
    config: RetryConfig | None = None, operation_name: str = "operation"
) -> Callable[..., Any]:
    """Decorator for retrying operations with configurable retry logic."""

    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(config.max_attempts),
            wait=wait_exponential(
                multiplier=config.wait_time, max=config.max_wait_time
            ),
            retry=retry_if_exception_type(config.retry_exceptions),
        )
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.log_warning_with_context(
                    "Retrying operation due to error",
                    context={
                        "operation": operation_name,
                        "error": str(e)
                    }
                )
                raise

        @retry(
            stop=stop_after_attempt(config.max_attempts),
            wait=wait_exponential(
                multiplier=config.wait_time, max=config.max_wait_time
            ),
            retry=retry_if_exception_type(config.retry_exceptions),
        )
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log_warning_with_context(
                    "Retrying operation due to error",
                    context={
                        "operation": operation_name,
                        "error": str(e)
                    }
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry_database_operation(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for retrying database operations."""
    config = RetryConfig(
        max_attempts=3,
        wait_time=0.5,
        max_wait_time=10.0,
        retry_exceptions=(ConnectionError, TimeoutError, OSError),
    )
    return retry_operation(config, "database_operation")(func)  # type: ignore


def retry_api_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for retrying API calls."""
    config = RetryConfig(
        max_attempts=3,
        wait_time=1.0,
        max_wait_time=30.0,
        retry_exceptions=(ConnectionError, TimeoutError, OSError),
    )
    return retry_operation(config, "api_call")(func)  # type: ignore


def retry_messaging_operation(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for retrying messaging operations."""
    config = RetryConfig(
        max_attempts=5,
        wait_time=0.5,
        max_wait_time=15.0,
        retry_exceptions=(ConnectionError, TimeoutError, OSError),
    )
    return retry_operation(config, "messaging_operation")(func)  # type: ignore


class RetryableOperation:
    """Base class for retryable operations."""

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()

    async def execute(
        self, operation: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute an operation with retry logic."""
        retry_func = retry_operation(self.config)(operation)
        return await retry_func(*args, **kwargs)

    def with_config(self, config: RetryConfig) -> "RetryableOperation":
        """Create a new instance with different configuration."""
        return RetryableOperation(config)


# Convenience functions
def retry_with_backoff(
    func: Callable[..., Any],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> Callable[..., Any]:
    """Retry function with exponential backoff."""
    config = RetryConfig(
        max_attempts=max_attempts, wait_time=base_delay, max_wait_time=max_delay
    )
    return retry_operation(config)(func)  # type: ignore


def retry_with_timeout(
    func: Callable[..., Any], timeout: float = 30.0, max_attempts: int = 3
) -> Callable[..., Any]:
    """Retry function with timeout."""
    config = RetryConfig(max_attempts=max_attempts, timeout=timeout)
    return retry_operation(config)(func)  # type: ignore
