"""Tests for the retry module."""

import asyncio
from typing import Any
from unittest.mock import patch

import pytest
from tenacity import RetryError

from eshop.core.retry.retry import (
    RetryableOperation,
    RetryConfig,
    retry_api_call,
    retry_database_operation,
    retry_messaging_operation,
    retry_operation,
    retry_with_backoff,
    retry_with_timeout,
)


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_retry_config_default_values(self) -> None:
        """Test RetryConfig with default values."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.wait_time == 1.0
        assert config.max_wait_time == 60.0
        assert config.retry_exceptions == (Exception,)
        assert config.timeout is None

    def test_retry_config_custom_values(self) -> None:
        """Test RetryConfig with custom values."""
        config = RetryConfig(
            max_attempts=5,
            wait_time=2.0,
            max_wait_time=30.0,
            retry_exceptions=(ValueError, TypeError),
            timeout=10.0,
        )

        assert config.max_attempts == 5
        assert config.wait_time == 2.0
        assert config.max_wait_time == 30.0
        assert config.retry_exceptions == (ValueError, TypeError)
        assert config.timeout == 10.0

    def test_retry_config_immutability(self) -> None:
        """Test that RetryConfig attributes can be modified."""
        config = RetryConfig()

        # Should be able to modify attributes
        config.max_attempts = 10
        config.wait_time = 5.0

        assert config.max_attempts == 10
        assert config.wait_time == 5.0


class TestRetryOperation:
    """Test retry_operation decorator."""

    def test_retry_operation_sync_function_success(self) -> None:
        """Test retry_operation with successful sync function."""
        call_count = 0

        def sync_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        decorated_func = retry_operation()(sync_func)
        result = decorated_func()

        assert result == "success"
        assert call_count == 1

    def test_retry_operation_sync_function_failure_then_success(self) -> None:
        """Test retry_operation with sync function that fails then succeeds."""
        call_count = 0

        def sync_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        decorated_func = retry_operation()(sync_func)
        result = decorated_func()

        assert result == "success"
        assert call_count == 3

    def test_retry_operation_sync_function_max_attempts_exceeded(self) -> None:
        """Test retry_operation with sync function that always fails."""
        call_count = 0

        def sync_func() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        decorated_func = retry_operation()(sync_func)

        with pytest.raises(RetryError):
            decorated_func()

        assert call_count == 3  # Default max_attempts

    def test_retry_operation_async_function_success(self) -> None:
        """Test retry_operation with successful async function."""
        call_count = 0

        async def async_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        decorated_func = retry_operation()(async_func)

        async def run_test() -> None:
            result = await decorated_func()
            assert result == "success"
            assert call_count == 1

        asyncio.run(run_test())

    def test_retry_operation_async_function_failure_then_success(self) -> None:
        """Test retry_operation with async function that fails then succeeds."""
        call_count = 0

        async def async_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        decorated_func = retry_operation()(async_func)

        async def run_test() -> None:
            result = await decorated_func()
            assert result == "success"
            assert call_count == 3

        asyncio.run(run_test())

    def test_retry_operation_async_function_max_attempts_exceeded(self) -> None:
        """Test retry_operation with async function that always fails."""
        call_count = 0

        async def async_func() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        decorated_func = retry_operation()(async_func)

        async def run_test() -> None:
            with pytest.raises(RetryError):
                await decorated_func()
            assert call_count == 3

        asyncio.run(run_test())

    def test_retry_operation_with_custom_config(self) -> None:
        """Test retry_operation with custom configuration."""
        call_count = 0

        def sync_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        config = RetryConfig(max_attempts=2, wait_time=0.1)
        decorated_func = retry_operation(config, "test_operation")(sync_func)
        result = decorated_func()

        assert result == "success"
        assert call_count == 2

    def test_retry_operation_with_specific_exceptions(self) -> None:
        """Test retry_operation with specific exception types."""
        call_count = 0

        def sync_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Retryable error")
            return "success"

        config = RetryConfig(retry_exceptions=(ValueError,))
        decorated_func = retry_operation(config)(sync_func)
        result = decorated_func()

        assert result == "success"
        assert call_count == 3

    def test_retry_operation_with_non_retryable_exception(self) -> None:
        """Test retry_operation with non-retryable exception."""
        call_count = 0

        def sync_func() -> str:
            nonlocal call_count
            call_count += 1
            raise TypeError("Non-retryable error")

        config = RetryConfig(retry_exceptions=(ValueError,))
        decorated_func = retry_operation(config)(sync_func)

        with pytest.raises(TypeError):
            decorated_func()

        assert call_count == 1  # Should not retry

    def test_retry_operation_logging(self) -> None:
        """Test that retry_operation logs warnings on failures."""
        call_count = 0

        def sync_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        with patch("eshop.core.retry.retry.logger") as mock_logger:
            decorated_func = retry_operation()(sync_func)
            result = decorated_func()

            assert result == "success"
            # Should log warnings for the first two failures
            assert mock_logger.warning.call_count == 2

    def test_retry_operation_preserves_function_metadata(self) -> None:
        """Test that retry_operation preserves function metadata."""

        def test_func(arg1: str, arg2: int = 42) -> str:
            """Test function docstring."""
            return f"{arg1}_{arg2}"

        decorated_func = retry_operation()(test_func)

        assert decorated_func.__name__ == "test_func"
        assert decorated_func.__doc__ == "Test function docstring."


class TestRetryableOperation:
    """Test RetryableOperation class."""

    def test_retryable_operation_init(self) -> None:
        """Test RetryableOperation initialization."""
        config = RetryConfig(max_attempts=5)
        retry_op = RetryableOperation(config)

        assert retry_op.config == config

    def test_retryable_operation_init_default_config(self) -> None:
        """Test RetryableOperation initialization with default config."""
        retry_op = RetryableOperation()

        assert isinstance(retry_op.config, RetryConfig)
        assert retry_op.config.max_attempts == 3

    def test_retryable_operation_execute_success(self) -> None:
        """Test RetryableOperation.execute with successful operation."""
        retry_op = RetryableOperation()

        async def test_operation() -> str:
            return "success"

        async def run_test() -> None:
            result = await retry_op.execute(test_operation)
            assert result == "success"

        asyncio.run(run_test())

    def test_retryable_operation_execute_with_retry(self) -> None:
        """Test RetryableOperation.execute with operation that needs retry."""
        retry_op = RetryableOperation()
        call_count = 0

        async def test_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        async def run_test() -> None:
            result = await retry_op.execute(test_operation)
            assert result == "success"
            assert call_count == 3

        asyncio.run(run_test())

    def test_retryable_operation_with_config(self) -> None:
        """Test RetryableOperation.with_config method."""
        original_config = RetryConfig(max_attempts=3)
        new_config = RetryConfig(max_attempts=5)

        retry_op = RetryableOperation(original_config)
        new_retry_op = retry_op.with_config(new_config)

        assert new_retry_op.config == new_config
        assert new_retry_op is not retry_op  # Should be a new instance


class TestConvenienceFunctions:
    """Test convenience retry functions."""

    def test_retry_database_operation(self) -> None:
        """Test retry_database_operation decorator."""
        call_count = 0

        def db_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Database connection failed")
            return "success"

        decorated_func = retry_database_operation(db_operation)
        result = decorated_func()

        assert result == "success"
        assert call_count == 3

    def test_retry_api_call(self) -> None:
        """Test retry_api_call decorator."""
        call_count = 0

        def api_call() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("API timeout")
            return "success"

        decorated_func = retry_api_call(api_call)
        result = decorated_func()

        assert result == "success"
        assert call_count == 3

    def test_retry_messaging_operation(self) -> None:
        """Test retry_messaging_operation decorator."""
        call_count = 0

        def messaging_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("Messaging connection failed")
            return "success"

        decorated_func = retry_messaging_operation(messaging_operation)
        result = decorated_func()

        assert result == "success"
        assert call_count == 3

    def test_retry_with_backoff(self) -> None:
        """Test retry_with_backoff function."""
        call_count = 0

        def test_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        decorated_func = retry_with_backoff(test_func, max_attempts=3, base_delay=0.1)
        result = decorated_func()

        assert result == "success"
        assert call_count == 3

    def test_retry_with_timeout(self) -> None:
        """Test retry_with_timeout function."""
        call_count = 0

        def test_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        decorated_func = retry_with_timeout(test_func, timeout=10.0, max_attempts=3)
        result = decorated_func()

        assert result == "success"
        assert call_count == 3


class TestRetryIntegration:
    """Integration tests for retry functionality."""

    def test_retry_with_different_exception_types(self) -> None:
        """Test retry behavior with different exception types."""
        call_count = 0

        def test_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection failed")
            elif call_count == 2:
                raise TimeoutError("Timeout")
            elif call_count == 3:
                raise OSError("OS error")
            return "success"

        config = RetryConfig(
            max_attempts=4, retry_exceptions=(ConnectionError, TimeoutError, OSError)
        )
        decorated_func = retry_operation(config)(test_func)
        result = decorated_func()

        assert result == "success"
        assert call_count == 4

    def test_retry_with_mixed_sync_async_operations(self) -> None:
        """Test retry with both sync and async operations."""
        # Test sync operation
        sync_call_count = 0

        def sync_func() -> str:
            nonlocal sync_call_count
            sync_call_count += 1
            if sync_call_count < 3:
                raise ValueError("Sync failure")
            return "sync_success"

        decorated_sync = retry_operation()(sync_func)
        sync_result = decorated_sync()
        assert sync_result == "sync_success"
        assert sync_call_count == 3

        # Test async operation
        async_call_count = 0

        async def async_func() -> str:
            nonlocal async_call_count
            async_call_count += 1
            if async_call_count < 3:
                raise ValueError("Async failure")
            return "async_success"

        decorated_async = retry_operation()(async_func)

        async def run_async_test() -> None:
            result = await decorated_async()
            assert result == "async_success"
            assert async_call_count == 3

        asyncio.run(run_async_test())

    def test_retry_configuration_validation(self) -> None:
        """Test retry configuration validation."""
        # Test with zero max_attempts
        config = RetryConfig(max_attempts=0)
        call_count = 0

        def test_func() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        decorated_func = retry_operation(config)(test_func)

        with pytest.raises(RetryError):
            decorated_func()

        assert call_count == 1  # Should not retry with 0 attempts

    def test_retry_with_function_arguments(self) -> None:
        """Test retry with functions that take arguments."""
        call_count = 0

        def test_func(name: str, count: int = 0) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return f"{name}_{count}"

        decorated_func = retry_operation()(test_func)
        result = decorated_func("test", 42)

        assert result == "test_42"
        assert call_count == 3

    def test_retry_with_keyword_arguments(self) -> None:
        """Test retry with functions that use keyword arguments."""
        call_count = 0

        def test_func(**kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return kwargs

        decorated_func = retry_operation()(test_func)
        result = decorated_func(name="test", value=42)

        assert result == {"name": "test", "value": 42}
        assert call_count == 3

    def test_retry_error_propagation(self) -> None:
        """Test that original error is preserved in retry failures."""
        call_count = 0

        def test_func() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Original error message")

        decorated_func = retry_operation()(test_func)

        with pytest.raises(RetryError) as exc_info:
            decorated_func()

        # The original error should be preserved in the last exception
        last_exception = exc_info.value.last_attempt.exception()
        assert isinstance(last_exception, ValueError)
        assert "Original error message" in str(last_exception)
        assert call_count == 3
