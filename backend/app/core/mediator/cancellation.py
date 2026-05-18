"""Cancellation token support for FastAPI with 1-1 parity to .NET CancellationToken."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from typing import Any

from app.core.logging.base_logger import BaseLogger
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


class CancellationToken:
    """Cancellation token equivalent to .NET CancellationToken with SQLAlchemy integration."""

    def __init__(
        self, request: Request | None = None, session: AsyncSession | None = None
    ) -> None:
        """Initialize cancellation token with optional database session."""
        self._request = request
        self._session = session
        self._cancelled = False
        self._completed = False  # Track if request completed successfully
        self._cleaning_up = False  # Track if cleanup is in progress
        self._logger = BaseLogger(__name__)
        self._monitor_task: asyncio.Task[None] | None = None
        self._rollback_callbacks: list[callable] = []

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
            while (
                not self._cancelled
                and not self._completed
                and not self._cleaning_up
                and self._request is not None
            ):
                if await self._request.is_disconnected():
                    # Only log and cancel if request disconnected BEFORE completion
                    if not self._completed and not self._cleaning_up:
                        self._cancelled = True
                        self._logger.log_debug_with_context(
                            "Request disconnected, cancellation token triggered"
                        )
                    break
                await asyncio.sleep(0.1)  # Check every 100ms
        except asyncio.CancelledError:
            # Task was cancelled during cleanup - this is expected
            pass
        except Exception as e:
            # Only log errors if not cleaning up
            if not self._cleaning_up:
                self._logger.log_error_with_context(
                    "Error monitoring request disconnection",
                    error=e,
                    context={"operation": "monitor_disconnection"},
                )
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
        """Manually cancel the token and trigger rollback."""
        self._cancelled = True
        self._logger.log_debug_with_context("Cancellation token manually cancelled")
        # Trigger rollback callbacks immediately
        asyncio.create_task(self._execute_rollback_callbacks())

    def mark_completed(self) -> None:
        """Mark the request as successfully completed to prevent false disconnection logs."""
        self._completed = True

    async def cleanup(self) -> None:
        """Clean up monitoring task and execute rollback if cancelled."""
        self._cleaning_up = True  # Signal that cleanup is in progress

        if self._cancelled:
            await self._execute_rollback_callbacks()

        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._monitor_task

    def register_rollback_callback(self, callback: callable) -> None:
        """Register a callback to be executed on cancellation for rollback."""
        self._rollback_callbacks.append(callback)

    async def _execute_rollback_callbacks(self) -> None:
        """Execute all registered rollback callbacks."""
        for callback in self._rollback_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                self._logger.log_error_with_context(
                    "Error executing rollback callback",
                    error=e,
                    context={"callback": str(callback)},
                )

    async def execute_with_rollback(self, operation: callable) -> Any:
        """Execute an operation with automatic rollback on cancellation."""
        try:
            # Register session rollback if session is available
            if self._session:
                self.register_rollback_callback(self._rollback_session)

            # Execute the operation
            if asyncio.iscoroutinefunction(operation):
                return await operation()
            else:
                return operation()

        except Exception:
            # If operation fails, trigger rollback
            if self._session:
                await self._rollback_session()
            raise

    async def _rollback_session(self) -> None:
        """Rollback the associated database session."""
        if self._session:
            try:
                await self._session.rollback()
                self._logger.log_debug_with_context(
                    "Database session rolled back due to cancellation"
                )
            except Exception as e:
                self._logger.log_error_with_context(
                    "Error rolling back database session", error=e
                )

    def get_session(self) -> AsyncSession | None:
        """Get the associated database session."""
        return self._session

    def set_session(self, session: AsyncSession) -> None:
        """Set the database session for this cancellation token."""
        self._session = session


class CancellationError(Exception):
    """Exception raised when operation is cancelled."""

    pass


@asynccontextmanager
async def create_cancellation_token(
    request: Request | None = None,
    session: AsyncSession | None = None,
) -> AsyncGenerator[CancellationToken, None]:
    """Create a cancellation token context manager."""
    token = CancellationToken(request, session)
    try:
        yield token
        # Mark as completed if we reach here (no exception)
        token.mark_completed()
    finally:
        await token.cleanup()


@asynccontextmanager
async def create_cancellation_token_with_session(
    request: Request,
    session: AsyncSession,
) -> AsyncGenerator[CancellationToken, None]:
    """Create a cancellation token context manager with database session for automatic rollback."""
    token = CancellationToken(request, session)
    try:
        yield token
        # Mark as completed if we reach here (no exception)
        token.mark_completed()
    finally:
        await token.cleanup()


def get_cancellation_token(
    request: Request, session: AsyncSession | None = None
) -> CancellationToken:
    """Get cancellation token from FastAPI request - matches .NET dependency injection pattern."""
    return CancellationToken(request, session)


def get_cancellation_token_with_session(
    request: Request, session: AsyncSession
) -> CancellationToken:
    """Get cancellation token with database session for automatic rollback."""
    return CancellationToken(request, session)


# Global cancellation token for operations not tied to HTTP requests
def get_global_cancellation_token(
    session: AsyncSession | None = None,
) -> CancellationToken:
    """Get global cancellation token for background operations."""
    return CancellationToken(session=session)
