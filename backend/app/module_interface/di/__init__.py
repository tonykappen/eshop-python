"""Dependency injection for global module interface."""

from app.module_interface.di.containers import Container
from app.module_interface.di.providers import (
    get_database_config,
    get_redis_config,
    get_rabbitmq_config,
    get_keycloak_config,
    get_logging_config,
    get_connection_string,
    create_container,
    configure_container,
    scan_assemblies,
    wire_container,
    get_container,
    get_service_provider,
)

__all__ = [
    "Container",
    "create_container",
    "configure_container",
    "scan_assemblies",
    "wire_container",
    "get_container",
    "get_service_provider",
    "get_database_config",
    "get_redis_config",
    "get_rabbitmq_config",
    "get_keycloak_config",
    "get_logging_config",
    "get_connection_string",
]

