"""Dependency injection container for basket module."""

import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BasketContainer:
    """Dependency injection container for basket module."""

    def __init__(self):
        """Initialize the container."""
        self._services: dict[type[Any], Any] = {}
        self._factories: dict[type[Any], Callable[[], Any]] = {}
        self._singletons: dict[type[Any], Any] = {}
        self._scoped: dict[type[Any], Any] = {}
        self._current_scope: str | None = None

    def register_singleton(self, service_type: type[T], instance: T) -> None:
        """
        Register a singleton service.

        Args:
            service_type: Type of service
            instance: Service instance
        """
        self._singletons[service_type] = instance
        logger.debug(f"Registered singleton: {service_type.__name__}")

    def register_factory(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory for a service.

        Args:
            service_type: Type of service
            factory: Factory function
        """
        self._factories[service_type] = factory
        logger.debug(f"Registered factory: {service_type.__name__}")

    def register_scoped(
        self, service_type: type[T], instance: T, scope: str = "default"
    ) -> None:
        """
        Register a scoped service.

        Args:
            service_type: Type of service
            instance: Service instance
            scope: Scope name
        """
        if scope not in self._scoped:
            self._scoped[scope] = {}
        self._scoped[scope][service_type] = instance
        logger.debug(
            f"Registered scoped service: {service_type.__name__} in scope {scope}"
        )

    def get(self, service_type: type[T]) -> T:
        """
        Get a service instance.

        Args:
            service_type: Type of service to get

        Returns:
            Service instance

        Raises:
            ValueError: If service is not registered
        """
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]

        # Check scoped services
        if self._current_scope and self._current_scope in self._scoped:
            if service_type in self._scoped[self._current_scope]:
                return self._scoped[self._current_scope][service_type]

        # Check factories
        if service_type in self._factories:
            instance = self._factories[service_type]()
            logger.debug(f"Created instance from factory: {service_type.__name__}")
            return instance

        # Check direct services
        if service_type in self._services:
            return self._services[service_type]

        raise ValueError(f"Service {service_type.__name__} is not registered")

    def register(self, service_type: type[T], instance: T) -> None:
        """
        Register a service instance.

        Args:
            service_type: Type of service
            instance: Service instance
        """
        self._services[service_type] = instance
        logger.debug(f"Registered service: {service_type.__name__}")


# Global container instance
@lru_cache(maxsize=1)
def get_basket_container() -> BasketContainer:
    """
    Get the global basket container instance.

    Returns:
        BasketContainer: Global container instance
    """
    return BasketContainer()
