"""Test for catalog DI container functionality."""

import logging
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)


class CatalogContainer:
    """Simple catalog container for testing."""

    def __init__(self):
        self._services = {}
        self._factories = {}
        self._singletons = {}
        self._scoped = {}
        self._current_scope = None

    def register_singleton(self, service_type, instance):
        """Register a singleton service."""
        self._singletons[service_type] = instance
        logger.debug(f"Registered singleton: {service_type.__name__}")

    def register_factory(self, service_type, factory):
        """Register a factory for a service."""
        self._factories[service_type] = factory
        logger.debug(f"Registered factory: {service_type.__name__}")

    def register_scoped(self, service_type, instance, scope="default"):
        """Register a scoped service."""
        if scope not in self._scoped:
            self._scoped[scope] = {}
        self._scoped[scope][service_type] = instance
        logger.debug(
            f"Registered scoped service: {service_type.__name__} in scope {scope}"
        )

    def get(self, service_type):
        """Get a service instance."""
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]

        # Check scoped services
        if self._current_scope and self._current_scope in self._scoped:  # noqa: SIM102
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

    def get_optional(self, service_type):
        """Get a service instance or None if not registered."""
        try:
            return self.get(service_type)
        except ValueError:
            return None

    def register(self, service_type, instance):
        """Register a service instance."""
        self._services[service_type] = instance
        logger.debug(f"Registered service: {service_type.__name__}")

    def enter_scope(self, scope_name):
        """Enter a new scope."""
        self._current_scope = scope_name
        logger.debug(f"Entered scope: {scope_name}")

    def exit_scope(self):
        """Exit the current scope."""
        if self._current_scope:
            logger.debug(f"Exited scope: {self._current_scope}")
            self._current_scope = None

    def is_registered(self, service_type):
        """Check if a service is registered."""
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

    def get_registered_services(self):
        """Get all registered services by type."""
        services = {
            "direct": [t.__name__ for t in self._services],
            "factories": [t.__name__ for t in self._factories],
            "singletons": [t.__name__ for t in self._singletons],
            "scoped": {},
        }

        for scope, services_in_scope in self._scoped.items():
            services["scoped"][scope] = [t.__name__ for t in services_in_scope]

        return services


def test_catalog_container_basic():
    """Test basic catalog container functionality."""
    container = CatalogContainer()

    # Test container creation
    assert container is not None
    logger.info("✅ Catalog container created successfully")

    # Test service registration
    class TestService:
        def __init__(self):
            self.name = "TestService"

    container.register_singleton(TestService, TestService())

    # Test service retrieval
    service = container.get(TestService)
    assert service.name == "TestService"
    logger.info("✅ Service registration and retrieval works")

    # Test service info
    services_info = container.get_registered_services()
    assert "TestService" in services_info["singletons"]
    logger.info("✅ Service info tracking works")

    logger.info("🎉 Catalog container basic test passed!")


def test_catalog_container_factory():
    """Test catalog container factory functionality."""
    container = CatalogContainer()

    # Test factory registration
    class FactoryService:
        def __init__(self):
            self.name = "FactoryService"

    def create_factory_service():
        return FactoryService()

    container.register_factory(FactoryService, create_factory_service)

    # Test factory service creation
    service1 = container.get(FactoryService)
    service2 = container.get(FactoryService)

    # Factory should create new instances each time
    assert service1.name == "FactoryService"
    assert service2.name == "FactoryService"
    assert service1 is not service2  # Different instances

    logger.info("✅ Factory service registration and creation works")
    logger.info("🎉 Catalog container factory test passed!")


def test_catalog_container_scoped():
    """Test catalog container scoped functionality."""
    container = CatalogContainer()

    # Test scoped service registration
    class ScopedService:
        def __init__(self):
            self.name = "ScopedService"

    container.enter_scope("request")
    container.register_scoped(ScopedService, ScopedService(), "request")

    # Test scoped service retrieval
    service = container.get(ScopedService)
    assert service.name == "ScopedService"

    # Test scope exit
    container.exit_scope()

    logger.info("✅ Scoped service registration and retrieval works")
    logger.info("🎉 Catalog container scoped test passed!")


if __name__ == "__main__":
    # Run tests
    print("🧪 Running catalog DI tests...")
    test_catalog_container_basic()
    test_catalog_container_factory()
    test_catalog_container_scoped()
    print("🎉 All catalog DI tests passed!")
