"""Registry for outbox publisher workers from all modules."""

from app.core.logging.base_logger import BaseLogger
from app.core.messaging.outbox import OutboxPublisherWorker

logger = BaseLogger(__name__)


class OutboxWorkerRegistry:
    """Registry for managing outbox publisher workers from all modules."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._workers: dict[str, OutboxPublisherWorker] = {}
        logger.log_debug_with_context("Outbox worker registry initialized")

    def register(self, module_name: str, worker: OutboxPublisherWorker) -> None:
        """
        Register an outbox publisher worker for a module.

        Args:
            module_name: Name of the module (e.g., 'catalog', 'basket', 'ordering')
            worker: Outbox publisher worker instance
        """
        if module_name in self._workers:
            logger.log_warning_with_context(
                "Worker for module already registered, overwriting",
                context={"module_name": module_name},
            )
        self._workers[module_name] = worker
        logger.log_with_context(
            "Registered outbox worker for module", context={"module_name": module_name}
        )

    def unregister(self, module_name: str) -> None:
        """
        Unregister an outbox publisher worker for a module.

        Args:
            module_name: Name of the module
        """
        if module_name in self._workers:
            del self._workers[module_name]
            logger.log_with_context(
                "Unregistered outbox worker for module",
                context={"module_name": module_name},
            )
        else:
            logger.log_warning_with_context(
                "No worker registered for module", context={"module_name": module_name}
            )

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
        logger.log_with_context(
            "Starting outbox publisher workers", context={"count": len(self._workers)}
        )
        for module_name, worker in self._workers.items():
            try:
                await worker.start()
                logger.log_with_context(
                    "Started outbox worker for module",
                    context={"module_name": module_name},
                )
            except Exception as e:
                logger.log_error_with_context(
                    "Failed to start outbox worker for module",
                    error=e,
                    context={"module_name": module_name},
                )
                raise

    async def stop_all(self) -> None:
        """Stop all registered outbox publisher workers."""
        logger.log_with_context(
            "Stopping outbox publisher workers", context={"count": len(self._workers)}
        )
        for module_name, worker in self._workers.items():
            try:
                await worker.stop()
                logger.log_with_context(
                    "Stopped outbox worker for module",
                    context={"module_name": module_name},
                )
            except Exception as e:
                logger.log_warning_with_context(
                    "Failed to stop outbox worker for module",
                    context={"module_name": module_name, "error": str(e)},
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
