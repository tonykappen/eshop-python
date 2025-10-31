"""Dependency injection container for catalog module."""

import logging
from typing import Any, Dict, Type, TypeVar, Optional, Callable
from functools import lru_cache

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CatalogContainer:
    """Dependency injection container for catalog module."""

    def __init__(self):
        """Initialize the container."""
        self._services: Dict[Type[Any], Any] = {}
        self._factories: Dict[Type[Any], Callable[[], Any]] = {}
        self._singletons: Dict[Type[Any], Any] = {}
        self._scoped: Dict[Type[Any], Any] = {}
        self._current_scope: Optional[str] = None

    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """
        Register a singleton service.
        
        Args:
            service_type: Type of service
            instance: Service instance
        """
        self._singletons[service_type] = instance
        logger.debug(f"Registered singleton: {service_type.__name__}")

    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory for a service.
        
        Args:
            service_type: Type of service
            factory: Factory function
        """
        self._factories[service_type] = factory
        logger.debug(f"Registered factory: {service_type.__name__}")

    def register_scoped(self, service_type: Type[T], instance: T, scope: str = "default") -> None:
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
        logger.debug(f"Registered scoped service: {service_type.__name__} in scope {scope}")

    def get(self, service_type: Type[T]) -> T:
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

    def get_optional(self, service_type: Type[T]) -> Optional[T]:
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

    def register(self, service_type: Type[T], instance: T) -> None:
        """
        Register a service instance.
        
        Args:
            service_type: Type of service
            instance: Service instance
        """
        self._services[service_type] = instance
        logger.debug(f"Registered service: {service_type.__name__}")

    def enter_scope(self, scope_name: str) -> None:
        """
        Enter a new scope.
        
        Args:
            scope_name: Name of the scope
        """
        self._current_scope = scope_name
        logger.debug(f"Entered scope: {scope_name}")

    def exit_scope(self) -> None:
        """Exit the current scope."""
        if self._current_scope:
            logger.debug(f"Exited scope: {self._current_scope}")
            self._current_scope = None

    def clear_scope(self, scope_name: str) -> None:
        """
        Clear a specific scope.
        
        Args:
            scope_name: Name of the scope to clear
        """
        if scope_name in self._scoped:
            del self._scoped[scope_name]
            logger.debug(f"Cleared scope: {scope_name}")

    def clear_all_scopes(self) -> None:
        """Clear all scoped services."""
        self._scoped.clear()
        logger.debug("Cleared all scopes")

    def is_registered(self, service_type: Type[T]) -> bool:
        """
        Check if a service is registered.
        
        Args:
            service_type: Type of service
            
        Returns:
            True if service is registered
        """
        return (
            service_type in self._services or
            service_type in self._factories or
            service_type in self._singletons or
            (self._current_scope and 
             self._current_scope in self._scoped and 
             service_type in self._scoped[self._current_scope])
        )

    def get_registered_services(self) -> Dict[str, list]:
        """
        Get all registered services by type.
        
        Returns:
            Dictionary of service types and their registration info
        """
        services = {
            "direct": [t.__name__ for t in self._services.keys()],
            "factories": [t.__name__ for t in self._factories.keys()],
            "singletons": [t.__name__ for t in self._singletons.keys()],
            "scoped": {}
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
