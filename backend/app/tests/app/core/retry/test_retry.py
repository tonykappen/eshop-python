"""Tests for retry utilities."""

import pytest
from app.core.retry.retry import (
    RetryConfig,
    RetryableOperation,
    retry_api_call,
    retry_database_operation,
    retry_messaging_operation,
    retry_operation,
    retry_with_backoff,
    retry_with_timeout,
)


class TestRetryConfig:
    def test_defaults(self) -> None:
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.wait_time == 1.0


class TestRetryOperation:
    def test_sync_retry_succeeds_after_failure(self) -> None:
        attempts = {"count": 0}

        @retry_operation(RetryConfig(max_attempts=3, wait_time=0.01), "sync_op")
        def flaky() -> str:
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise ConnectionError("temporary")
            return "ok"

        assert flaky() == "ok"
        assert attempts["count"] == 2

    @pytest.mark.asyncio
    async def test_async_retry_succeeds(self) -> None:
        attempts = {"count": 0}

        @retry_operation(RetryConfig(max_attempts=2, wait_time=0.01), "async_op")
        async def flaky_async() -> int:
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise TimeoutError("temporary")
            return 42

        assert await flaky_async() == 42


class TestRetryDecorators:
    def test_database_decorator(self) -> None:
        @retry_database_operation
        def db_op() -> str:
            return "db"

        assert db_op() == "db"

    def test_api_decorator(self) -> None:
        @retry_api_call
        def api_op() -> str:
            return "api"

        assert api_op() == "api"

    def test_messaging_decorator(self) -> None:
        @retry_messaging_operation
        def msg_op() -> str:
            return "msg"

        assert msg_op() == "msg"


class TestRetryableOperation:
    @pytest.mark.asyncio
    async def test_execute_with_config(self) -> None:
        op = RetryableOperation(RetryConfig(max_attempts=1))

        async def run() -> str:
            return "done"

        result = await op.execute(run)
        assert result == "done"

    def test_with_config_returns_new_instance(self) -> None:
        base = RetryableOperation()
        updated = base.with_config(RetryConfig(max_attempts=5))
        assert updated.config.max_attempts == 5


class TestConvenienceRetry:
    def test_retry_with_backoff(self) -> None:
        @retry_with_backoff
        def fn() -> bool:
            return True

        assert fn() is True

    def test_retry_with_timeout(self) -> None:
        @retry_with_timeout
        def fn() -> bool:
            return True

        assert fn() is True
