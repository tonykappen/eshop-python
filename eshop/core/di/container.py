"""Dependency injection container with assembly scanning support."""

from typing import Any

from dependency_injector import containers, providers

from ..logging.logger import get_logger
from .assembly_scanner import AssemblyScanner

logger = get_logger(__name__)


class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""

    # Configuration
    config = providers.Configuration()

    # Core services
    logger = providers.Singleton(lambda: get_logger("eshop"))

    # Assembly scanner
    assembly_scanner = providers.Singleton(AssemblyScanner, container=providers.Self())


class ServiceProvider:
    """Service provider for retrieving services from the container."""

    def __init__(self, container: Container):
        self.container = container

    def get_service(self, service_name: str) -> Any:
        """Get a service by name."""
        if hasattr(self.container, service_name):
            return getattr(self.container, service_name)()
        else:
            raise ValueError(f"Service '{service_name}' not found")

    def get_required_service(self, service_type: type) -> Any:
        """Get a service by type."""
        for _name, provider in self.container.providers.items():
            if hasattr(provider, "provides") and provider.provides == service_type:
                return provider()

        raise ValueError(f"Service of type '{service_type.__name__}' not found")

    def get_optional_service(self, service_type: type) -> Any | None:
        """Get a service by type, returning None if not found."""
        try:
            return self.get_required_service(service_type)
        except ValueError:
            return None


def create_container() -> Container:
    """Create and configure the main container."""
    container = Container()

    # Configure the container
    container.config.from_dict(
        {
            "database": {"connection_string": "postgresql://user:pass@localhost/db"},
            "redis": {"connection_string": "redis://localhost:6379"},
            "rabbitmq": {"connection_string": "amqp://guest:guest@localhost:5672/"},
        }
    )

    return container


def configure_container(container: Container, config_dict: dict[str, Any]) -> None:
    """Configure the container with settings."""
    container.config.from_dict(config_dict)


def scan_assemblies(container: Container, packages: list) -> None:
    """Scan packages for automatic service registration."""
    scanner = container.assembly_scanner()

    for package in packages:
        try:
            scanner.scan_package(package)
            logger.info(f"Scanned package: {package}")
        except Exception as e:
            logger.error(f"Failed to scan package {package}: {e}")


def wire_container(container: Container, packages: list) -> None:
    """Wire the container with packages for dependency injection."""
    container.wire(packages=packages)
    logger.info(f"Wired container with packages: {packages}")


# Convenience functions
def get_container() -> Container:
    """Get the global container instance."""
    return create_container()


def get_service_provider(container: Container) -> ServiceProvider:
    """Get a service provider for the container."""
    return ServiceProvider(container)
