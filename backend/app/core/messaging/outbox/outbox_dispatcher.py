"""Outbox dispatcher - background worker that publishes and marks processed."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class IOutboxDispatcher(ABC):
    """Interface for outbox dispatcher."""

    @abstractmethod
    async def start(self) -> None:
        """Start the outbox dispatcher."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the outbox dispatcher."""
        pass

    @abstractmethod
    async def publish_pending_messages(self) -> None:
        """Publish all pending messages from outbox."""
        pass


class OutboxDispatcher(IOutboxDispatcher):
    """Background dispatcher that reads Outbox rows, publishes events, and marks them as processed."""

    def __init__(
        self,
        session_factory: Any,
        event_publisher: Any,
        batch_size: int = 10,
        poll_interval: float = 5.0,
        max_retries: int = 3,
    ):
        """
        Initialize the outbox dispatcher.

        Args:
            session_factory: Factory for creating database sessions
            event_publisher: Event publisher for publishing integration events
            batch_size: Number of messages to process in each batch
            poll_interval: Interval between polls in seconds
            max_retries: Maximum number of retries for failed messages
        """
        self.session_factory = session_factory
        self.event_publisher = event_publisher
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.is_running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the outbox dispatcher."""
        if self.is_running:
            logger.log_warning_with_context("Outbox dispatcher is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.log_with_context("Outbox dispatcher started")

    async def stop(self) -> None:
        """Stop the outbox dispatcher."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.log_with_context("Outbox dispatcher stopped")

    async def _run_loop(self) -> None:
        """Main loop for processing outbox messages."""
        while self.is_running:
            try:
                await self.publish_pending_messages()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.log_error_with_context(
                "Error in outbox dispatcher loop",
                error=e
            )
                await asyncio.sleep(self.poll_interval)

    async def publish_pending_messages(self) -> None:
        """Publish all pending messages from outbox."""
        # This should be implemented by modules using their ORM model
        # The dispatcher will query for pending messages and publish them
        logger.log_debug_with_context("Publishing pending outbox messages")

        # Example implementation:
        # async with self.session_factory() as session:
        #     # Query pending messages
        #     # For each message:
        #     #   1. Mark as processing
        #     #   2. Publish to event bus
        #     #   3. Mark as published (or failed)
        #     pass
