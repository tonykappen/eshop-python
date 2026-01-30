"""Registry for outbox publisher workers from all modules."""

import logging
from typing import Any

from app.core.messaging.outbox import OutboxPublisherWorker

logger = logging.getLogger(__name__)


class OutboxWorkerRegistry:
    """Registry for managing outbox publisher workers from all modules."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._workers: dict[str, OutboxPublisherWorker] = {}
        logger.debug("Outbox worker registry initialized")

    def register(self, module_name: str, worker: OutboxPublisherWorker) -> None:
        """
        Register an outbox publisher worker for a module.

        Args:
            module_name: Name of the module (e.g., 'catalog', 'basket', 'ordering')
            worker: Outbox publisher worker instance
        """
        if module_name in self._workers:
            logger.warning(
                f"Worker for module '{module_name}' already registered, overwriting"
            )
        self._workers[module_name] = worker
        logger.info(f"Registered outbox worker for module: {module_name}")

    def unregister(self, module_name: str) -> None:
        """
        Unregister an outbox publisher worker for a module.

        Args:
            module_name: Name of the module
        """
        if module_name in self._workers:
            del self._workers[module_name]
            logger.info(f"Unregistered outbox worker for module: {module_name}")
        else:
            logger.warning(f"No worker registered for module: {module_name}")

    def get(self, module_name: str) -> OutboxPublisherWorker | None:
        """
        Get the outbox publisher worker for a module.

        Args:
            module_name: Name of the module

        Returns:
            Outbox publisher worker instance or None if not registered
        """
        return self._workers.get(module_name)

    def get_all(self) -> dict[str, OutboxPublisherWorker]:
        """
        Get all registered workers.

        Returns:
            Dictionary mapping module names to worker instances
        """
        return self._workers.copy()

    async def start_all(self) -> None:
        """Start all registered outbox publisher workers."""
        logger.info(f"Starting {len(self._workers)} outbox publisher worker(s)")
        for module_name, worker in self._workers.items():
            try:
                await worker.start()
                logger.info(f"Started outbox worker for module: {module_name}")
            except Exception as e:
                logger.error(
                    f"Failed to start outbox worker for module '{module_name}': {e}"
                )
                raise

    async def stop_all(self) -> None:
        """Stop all registered outbox publisher workers."""
        logger.info(f"Stopping {len(self._workers)} outbox publisher worker(s)")
        for module_name, worker in self._workers.items():
            try:
                await worker.stop()
                logger.info(f"Stopped outbox worker for module: {module_name}")
            except Exception as e:
                logger.warning(
                    f"Failed to stop outbox worker for module '{module_name}': {e}"
                )

    def is_registered(self, module_name: str) -> bool:
        """
        Check if a worker is registered for a module.

        Args:
            module_name: Name of the module

        Returns:
            True if registered, False otherwise
        """
        return module_name in self._workers


# Global registry instance
outbox_worker_registry = OutboxWorkerRegistry()
