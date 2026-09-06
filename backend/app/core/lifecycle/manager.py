"""Application lifecycle manager for graceful startup and shutdown."""

import asyncio
import signal
import sys
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from typing import Any

from app.core.logging.base_logger import BaseLogger
from fastapi import FastAPI

logger = BaseLogger(__name__)

# Type alias for async lifecycle callbacks
LifecycleCallback = Callable[[], Awaitable[None]]


class LifecycleManager:
    """Manages application lifecycle with graceful startup and shutdown."""

    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self.startup_callbacks: list[LifecycleCallback] = []
        self.shutdown_callbacks: list[LifecycleCallback] = []
        self.is_shutting_down: bool = False
        self.shutdown_timeout: float = 30.0
        self._shutdown_event: asyncio.Event | None = None

    def add_startup_callback(self, callback: LifecycleCallback) -> None:
        """Add a callback to be executed during startup."""
        self.startup_callbacks.append(callback)
        logger.log_debug_with_context(
            "Added startup callback", context={"callback_name": callback.__name__}
        )

    def add_shutdown_callback(self, callback: LifecycleCallback) -> None:
        """Add a callback to be executed during shutdown."""
        self.shutdown_callbacks.append(callback)
        logger.log_debug_with_context(
            "Added shutdown callback", context={"callback_name": callback.__name__}
        )

    def set_shutdown_timeout(self, timeout: float) -> None:
        """Set the timeout for graceful shutdown in seconds."""
        self.shutdown_timeout = timeout
        logger.log_debug_with_context(
            "Shutdown timeout set", context={"timeout_seconds": timeout}
        )

    async def startup(self) -> None:
        """Execute all startup callbacks in sequence."""
        logger.log_with_context("Starting application lifecycle...", "info")

        for i, callback in enumerate(self.startup_callbacks):
            try:
                logger.log_with_context(
                    "Executing startup callback",
                    "info",
                    context={
                        "callback_index": i + 1,
                        "total_callbacks": len(self.startup_callbacks),
                        "callback_name": callback.__name__,
                    },
                )
                await callback()
                logger.log_with_context(
                    "[OK] Startup callback completed successfully",
                    "info",
                    context={"callback_name": callback.__name__},
                )
            except Exception as e:
                logger.log_error_with_context(
                    "[FAILED] Startup callback failed",
                    error=e,
                    context={"callback_name": callback.__name__},
                )
                # Re-raise to prevent application from starting with failed dependencies
                raise RuntimeError(
                    f"Startup failed in callback {callback.__name__}: {e}"
                ) from e

        logger.log_with_context(
            "[OK] Application startup completed successfully", "info"
        )

    async def shutdown(self) -> None:
        """Execute all shutdown callbacks in sequence with timeout protection."""
        if self.is_shutting_down:
            logger.log_warning_with_context(
                "Shutdown already in progress, ignoring duplicate shutdown request"
            )
            return

        self.is_shutting_down = True
        logger.log_with_context("[SHUTDOWN] Starting graceful shutdown...", "info")

        # Execute shutdown callbacks in reverse order (LIFO)
        shutdown_tasks = []
        for i, callback in enumerate(reversed(self.shutdown_callbacks)):
            callback_name = callback.__name__
            logger.log_with_context(
                "Executing shutdown callback",
                "info",
                context={
                    "callback_index": i + 1,
                    "total_callbacks": len(self.shutdown_callbacks),
                    "callback_name": callback_name,
                },
            )

            try:
                # Wrap each callback with timeout protection
                shutdown_task = asyncio.create_task(
                    asyncio.wait_for(
                        callback(),
                        timeout=self.shutdown_timeout / len(self.shutdown_callbacks),
                    )
                )
                shutdown_tasks.append((callback_name, shutdown_task))
            except Exception as e:
                logger.log_error_with_context(
                    "[FAILED] Failed to create shutdown task",
                    error=e,
                    context={"callback_name": callback_name},
                )

        # Wait for all shutdown tasks with overall timeout
        if shutdown_tasks:
            try:
                logger.log_with_context(
                    "Waiting for shutdown tasks to complete",
                    "info",
                    context={"task_count": len(shutdown_tasks)},
                )
                await asyncio.wait_for(
                    self._execute_shutdown_tasks(shutdown_tasks),
                    timeout=self.shutdown_timeout,
                )
            except TimeoutError:
                logger.log_error_with_context(
                    f"[TIMEOUT] Shutdown timeout ({self.shutdown_timeout}s) exceeded, forcing exit"
                )
                for callback_name, task in shutdown_tasks:
                    if not task.done():
                        logger.log_warning_with_context(
                            f"Force cancelling shutdown task: {callback_name}"
                        )
                        task.cancel()

        logger.log_with_context("[OK] Graceful shutdown completed", "info")

    async def _execute_shutdown_tasks(
        self, shutdown_tasks: list[tuple[str, asyncio.Task[None]]]
    ) -> None:
        """Execute shutdown tasks and handle their completion."""
        for callback_name, task in shutdown_tasks:
            try:
                await task
                logger.log_with_context(
                    f"[OK] Shutdown callback {callback_name} completed successfully",
                    "info",
                )
            except asyncio.CancelledError:
                logger.log_warning_with_context(
                    f"[WARNING] Shutdown callback {callback_name} was cancelled"
                )
            except Exception as e:
                logger.log_error_with_context(
                    "[FAILED] Shutdown callback failed",
                    error=e,
                    context={"callback_name": callback_name},
                )
                # Continue with other shutdown tasks even if one fails

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        if sys.platform == "win32":
            logger.log_warning_with_context(
                "Signal handlers not fully supported on Windows"
            )
            return

        self._shutdown_event = asyncio.Event()

        def signal_handler(signum: int, frame: Any) -> None:  # noqa: ARG001
            """Handle shutdown signals."""
            signal_name = signal.Signals(signum).name
            logger.log_with_context(
                "[SIGNAL] Received signal, initiating graceful shutdown",
                "info",
                context={"signal_name": signal_name, "signal_number": signum},
            )

            if self._shutdown_event:
                self._shutdown_event.set()

        # Register signal handlers
        for sig in [signal.SIGTERM, signal.SIGINT]:
            try:
                signal.signal(sig, signal_handler)
                logger.log_debug_with_context(
                    "Registered signal handler",
                    context={"signal_name": signal.Signals(sig).name},
                )
            except (OSError, ValueError) as e:
                logger.log_warning_with_context(
                    "Could not register signal handler",
                    context={"signal_name": signal.Signals(sig).name, "error": str(e)},
                )

    @asynccontextmanager
    async def lifespan_context(
        self,
        app: FastAPI,  # noqa: ARG002
    ) -> AsyncGenerator[None, None]:
        """Create an async context manager for FastAPI lifespan management."""
        shutdown_task: asyncio.Task[None] | None = None

        try:
            # Setup signal handlers
            self.setup_signal_handlers()

            # Execute startup sequence
            await self.startup()

            logger.log_with_context(
                "[READY] Application is ready to serve requests", "info"
            )

            # Create background task to monitor for shutdown signals
            if self._shutdown_event:
                shutdown_task = asyncio.create_task(self._wait_for_shutdown_signal())

            yield

        except Exception as e:
            logger.log_error_with_context(
                "[ERROR] Error during application startup", error=e
            )
            raise
        finally:
            # Cancel shutdown monitoring task
            if shutdown_task and not shutdown_task.done():
                shutdown_task.cancel()
                with suppress(asyncio.CancelledError):
                    await shutdown_task

            # Execute shutdown sequence
            await self.shutdown()

    async def _wait_for_shutdown_signal(self) -> None:
        """Wait for shutdown signal in the background."""
        if self._shutdown_event:
            try:
                await self._shutdown_event.wait()
                logger.log_with_context(
                    "[SHUTDOWN] Shutdown signal received, starting graceful shutdown",
                    "info",
                )
            except asyncio.CancelledError:
                logger.log_debug_with_context(
                    "Shutdown signal monitoring task was cancelled"
                )


# Global lifecycle manager instance
lifecycle_manager = LifecycleManager()


def register_startup_callback(callback: LifecycleCallback) -> None:
    """Register a startup callback with the global lifecycle manager."""
    lifecycle_manager.add_startup_callback(callback)


def register_shutdown_callback(callback: LifecycleCallback) -> None:
    """Register a shutdown callback with the global lifecycle manager."""
    lifecycle_manager.add_shutdown_callback(callback)


def set_shutdown_timeout(timeout: float) -> None:
    """Set the shutdown timeout for the global lifecycle manager."""
    lifecycle_manager.set_shutdown_timeout(timeout)
