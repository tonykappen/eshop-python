"""DI provider logic for core services."""


from app.core.di.container import (
    Container,
    configure_container,
    create_container,
    get_connection_string,
    get_database_config,
    get_keycloak_config,
    get_logging_config,
    get_rabbitmq_config,
    get_redis_config,
    get_service_provider,
    scan_assemblies,
    wire_container,
)

# Re-export convenience functions
__all__ = [
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


def get_container() -> Container:
    """Get the global container instance."""
    return create_container()
