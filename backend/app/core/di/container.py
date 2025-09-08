"""Dependency injection container with assembly scanning support."""

from typing import Any

from dependency_injector import containers, providers

from ..logging.base_logger import BaseLogger
from .assembly_scanner import AssemblyScanner
from ...config.settings import settings

logger = BaseLogger(__name__)


class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""

    # Configuration
    config = providers.Configuration()

    # Core services
    logger = providers.Singleton(lambda: BaseLogger("eshop"))

    # Assembly scanner - will be set after container creation
    assembly_scanner = providers.Singleton(AssemblyScanner, container=None)


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

    # Configure the container using settings
    container.config.from_dict(
        {
            "database": {
                "connection_string": settings.database_connection_string,
                "host": settings.database_host,
                "port": settings.database_port,
                "name": settings.database_name,
                "user": settings.database_user,
                "password": settings.database_password,
            },
            "redis": {
                "connection_string": settings.redis_connection_string,
                "host": settings.redis_host,
                "port": settings.redis_port,
                "db": settings.redis_db,
            },
            "rabbitmq": {
                "connection_string": settings.rabbitmq_connection_string,
                "host": settings.rabbitmq_host,
                "port": settings.rabbitmq_port,
                "user": settings.rabbitmq_user,
                "password": settings.rabbitmq_password,
            },
            "keycloak": {
                "server_url": settings.keycloak_server_url,
                "realm": settings.keycloak_realm,
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
                "callback_uri": settings.keycloak_callback_uri,
            },
            "logging": {
                "level": settings.log_level,
                "enable_seq": settings.log_enable_seq,
                "seq_url": settings.seq_url,
                "seq_api_key": settings.seq_api_key,
                "enable_file": settings.log_enable_file,
                "directory": settings.log_directory,
                "separate_server_logs": settings.log_separate_server_logs,
                "enable_request_logging": settings.log_enable_request_logging,
                "request_body": settings.log_request_body,
                "response_body": settings.log_response_body,
            },
        }
    )

    # Fix the assembly scanner container reference
    scanner = container.assembly_scanner()
    scanner.container = container

    return container


def configure_container(container: Container, config_dict: dict[str, Any]) -> None:
    """Configure the container with settings."""
    container.config.from_dict(config_dict)


def scan_assemblies(container: Container, packages: list) -> None:
    """Scan packages for automatic service registration."""
    scanner = container.assembly_scanner()

    # Ensure scanner has container reference
    if scanner.container is None:
        scanner.container = container

    for package in packages:
        try:
            scanner.scan_package(package)
            logger.info(f"Scanned package: {package}")
        except Exception as e:
            logger.error(f"Failed to scan package {package}: {e}")


def wire_container(container: Container, packages: list) -> None:
    """Wire the container with packages for dependency injection."""
    try:
        container.wire(packages=packages)
        logger.info(f"Wired container with packages: {packages}")
    except Exception as e:
        logger.warning(f"Container wiring failed: {e}")
        # Don't re-raise - let the application continue without wiring


# Convenience functions
def get_container() -> Container:
    """Get the global container instance."""
    return create_container()


def get_service_provider(container: Container) -> ServiceProvider:
    """Get a service provider for the container."""
    return ServiceProvider(container)


def get_database_config(container: Container) -> dict[str, Any]:
    """Get database configuration from container."""
    return container.config.database()


def get_redis_config(container: Container) -> dict[str, Any]:
    """Get Redis configuration from container."""
    return container.config.redis()


def get_rabbitmq_config(container: Container) -> dict[str, Any]:
    """Get RabbitMQ configuration from container."""
    return container.config.rabbitmq()


def get_keycloak_config(container: Container) -> dict[str, Any]:
    """Get Keycloak configuration from container."""
    return container.config.keycloak()


def get_logging_config(container: Container) -> dict[str, Any]:
    """Get logging configuration from container."""
    return container.config.logging()


def get_connection_string(container: Container, service: str) -> str:
    """Get connection string for a specific service."""
    service_config = getattr(container.config, service)()
    return service_config.get("connection_string", "")
