"""Cancellation token support for FastAPI with 1-1 parity to .NET CancellationToken."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from fastapi import Request

from app.core.logging.logger import get_logger


class CancellationToken:
    """Cancellation token equivalent to .NET CancellationToken."""

    def __init__(self, request: Request | None = None) -> None:
        """Initialize cancellation token."""
        self._request = request
        self._cancelled = False
        self._logger = get_logger(__name__)
        self._monitor_task: asyncio.Task[None] | None = None

        # Create a task to monitor request disconnection
        if request:
            self._start_monitoring()

    def _start_monitoring(self) -> None:
        """Start monitoring for request cancellation."""
        if self._request:
            self._monitor_task = asyncio.create_task(self._monitor_disconnection())

    async def _monitor_disconnection(self) -> None:
        """Monitor for request disconnection."""
        try:
            while not self._cancelled and self._request is not None:
                if await self._request.is_disconnected():
                    self._cancelled = True
                    self._logger.debug(
                        "Request disconnected, cancellation token triggered"
                    )
                    break
                await asyncio.sleep(0.1)  # Check every 100ms
        except Exception as e:
            self._logger.error(f"Error monitoring request disconnection: {e}")
            self._cancelled = True

    @property
    def is_cancellation_requested(self) -> bool:
        """Check if cancellation has been requested - matches .NET CancellationToken.IsCancellationRequested."""
        return self._cancelled

    def throw_if_cancellation_requested(self) -> None:
        """Throw if cancellation has been requested - matches .NET CancellationToken.ThrowIfCancellationRequested()."""
        if self._cancelled:
            raise CancellationError("Operation was cancelled")

    async def wait_for_cancellation(self) -> None:
        """Wait for cancellation to be requested."""
        while not self._cancelled:
            await asyncio.sleep(0.1)

    def cancel(self) -> None:
        """Manually cancel the token."""
        self._cancelled = True
        self._logger.debug("Cancellation token manually cancelled")

    async def cleanup(self) -> None:
        """Clean up monitoring task."""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._monitor_task


class CancellationError(Exception):
    """Exception raised when operation is cancelled."""

    pass


@asynccontextmanager
async def create_cancellation_token(
    request: Request | None = None,
) -> AsyncGenerator[CancellationToken, None]:
    """Create a cancellation token context manager."""
    token = CancellationToken(request)
    try:
        yield token
    finally:
        await token.cleanup()


def get_cancellation_token(request: Request) -> CancellationToken:
    """Get cancellation token from FastAPI request - matches .NET dependency injection pattern."""
    return CancellationToken(request)


# Global cancellation token for operations not tied to HTTP requests
def get_global_cancellation_token() -> CancellationToken:
    """Get global cancellation token for background operations."""
    return CancellationToken()
