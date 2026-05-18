"""Dependency injection container for catalog module."""

from collections.abc import Callable
from functools import lru_cache
from typing import Any, TypeVar

from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)

T = TypeVar("T")


class CatalogContainer:
    """Dependency injection container for catalog module."""

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
        logger.log_debug_with_context(
            "Registered singleton", context={"service_type": service_type.__name__}
        )

    def register_factory(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory for a service.

        Args:
            service_type: Type of service
            factory: Factory function
        """
        self._factories[service_type] = factory
        logger.log_debug_with_context(
            "Registered factory", context={"service_type": service_type.__name__}
        )

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
        logger.log_debug_with_context(
            "Registered scoped service",
            context={"service_type": service_type.__name__, "scope": scope},
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
            logger.log_debug_with_context(
                "Created instance from factory",
                context={"service_type": service_type.__name__},
            )
            return instance

        # Check direct services
        if service_type in self._services:
            return self._services[service_type]

        raise ValueError(f"Service {service_type.__name__} is not registered")

    def get_optional(self, service_type: type[T]) -> T | None:
        """
        Get a service instance or None if not registered.

        Args:
            service_type: Type of service to get

        Returns:
            Service instance or None
        """
        try:
            return self.get(service_type)
        except ValueError:
            return None

    def register(self, service_type: type[T], instance: T) -> None:
        """
        Register a service instance.

        Args:
            service_type: Type of service
            instance: Service instance
        """
        self._services[service_type] = instance
        logger.log_debug_with_context(
            "Registered service", context={"service_type": service_type.__name__}
        )

    def enter_scope(self, scope_name: str) -> None:
        """
        Enter a new scope.

        Args:
            scope_name: Name of the scope
        """
        self._current_scope = scope_name
        logger.log_debug_with_context(
            "Entered scope", context={"scope_name": scope_name}
        )

    def exit_scope(self) -> None:
        """Exit the current scope."""
        if self._current_scope:
            logger.log_debug_with_context(
                "Exited scope", context={"scope_name": self._current_scope}
            )
            self._current_scope = None

    def clear_scope(self, scope_name: str) -> None:
        """
        Clear a specific scope.

        Args:
            scope_name: Name of the scope to clear
        """
        if scope_name in self._scoped:
            del self._scoped[scope_name]
            logger.log_debug_with_context(
                "Cleared scope", context={"scope_name": scope_name}
            )

    def clear_all_scopes(self) -> None:
        """Clear all scoped services."""
        self._scoped.clear()
        logger.log_debug_with_context("Cleared all scopes")

    def is_registered(self, service_type: type[T]) -> bool:
        """
        Check if a service is registered.

        Args:
            service_type: Type of service

        Returns:
            True if service is registered
        """
        return (
            service_type in self._services
            or service_type in self._factories
            or service_type in self._singletons
            or (
                self._current_scope
                and self._current_scope in self._scoped
                and service_type in self._scoped[self._current_scope]
            )
        )

    def get_registered_services(self) -> dict[str, list]:
        """
        Get all registered services by type.

        Returns:
            Dictionary of service types and their registration info
        """
        services = {
            "direct": [t.__name__ for t in self._services.keys()],
            "factories": [t.__name__ for t in self._factories.keys()],
            "singletons": [t.__name__ for t in self._singletons.keys()],
            "scoped": {},
        }

        for scope, services_in_scope in self._scoped.items():
            services["scoped"][scope] = [t.__name__ for t in services_in_scope.keys()]

        return services


# Global container instance
@lru_cache(maxsize=1)
def get_catalog_container() -> CatalogContainer:
    """
    Get the global catalog container instance.

    Returns:
        CatalogContainer: Global container instance
    """
    return CatalogContainer()
