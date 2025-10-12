"""Application initialization functions for eShop Modular Monolith."""

from app.config.settings import settings
from app.core.di.container import create_container, scan_assemblies, wire_container
from app.core.logging.base_logger import BaseLogger
from app.core.logging.logger import configure_logging
from app.core.mediator.fastapi_integration import configure_mediator


async def initialize_logging() -> None:
    """Initialize and configure application logging with async dispatcher."""
    logger = BaseLogger("initialization")
    logger.log_with_context("Initializing logging configuration", "info")

    # Configure logging first (handlers, formatters, etc.)
    configure_logging(
        log_level=settings.log_level,
        log_format="json",
        enable_seq=settings.log_enable_seq,
        seq_url=settings.seq_url,
        seq_api_key=settings.seq_api_key,
        enable_file_logging=settings.log_enable_file,
        log_directory=settings.log_directory,
        separate_server_logs=settings.log_separate_server_logs,
        enable_console=True,  # Always enable console output
        environment=settings.environment,
    )

    # Initialize async CLEF dispatcher for Seq
    if settings.log_enable_seq:
        try:
            from app.core.logging.clef_dispatcher import init_dispatcher
            
            dispatcher = await init_dispatcher(
                seq_url=settings.seq_url,
                seq_api_key=settings.seq_api_key,
                log_directory=settings.log_directory,
                queue_max_size=10000,
                batch_size=50,
                flush_interval=1.0,
            )
            
            logger.log_with_context(
                "Async CLEF dispatcher initialized successfully",
                "info",
                context={"seq_url": settings.seq_url},
            )
        except Exception as e:
            logger.log_error_with_context(
                "Failed to initialize async CLEF dispatcher",
                error=e,
            )

    logger.log_with_context("Logging configuration completed", "info")


async def initialize_dependency_injection() -> None:
    """Initialize dependency injection container."""
    logger = BaseLogger("initialization")
    logger.log_with_context("Initializing dependency injection container", "info")

    # Initialize DI container
    container = create_container()
    container.config.from_dict(
        {
            "database": {"connection_string": settings.database_connection_string},
            "redis": {"connection_string": settings.redis_connection_string},
            "rabbitmq": {"connection_string": settings.rabbitmq_connection_string},
            "keycloak": {
                "server_url": settings.keycloak_server_url,
                "realm": settings.keycloak_realm,
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
            },
        }
    )

    # Scan assemblies for automatic service registration
    scan_assemblies(
        container,
        ["app.modules.catalog", "app.modules.basket", "app.modules.ordering"],
    )

    # Wire container with packages (after services are registered)
    try:
        wire_container(
            container,
            ["app.modules.catalog", "app.modules.basket", "app.modules.ordering"],
        )
    except Exception as e:
        logger.log_warning_with_context(
            "Container wiring failed (non-critical)", context={"error": str(e)}
        )
        # Continue without wiring - services can still be accessed directly

    # Store container in global variable for access in main.py
    global _app_container
    _app_container = container

    logger.log_with_context("Dependency injection container initialized", "info")


# Global container reference for lifecycle management
_app_container = None


def get_app_container():
    """Get the application container instance."""
    return _app_container


async def initialize_mediator() -> None:
    """Initialize mediator pattern - matches .NET AddMediatRWithAssemblies()."""
    logger = BaseLogger("initialization")
    logger.log_with_context("Initializing mediator pattern", "info")

    # Configure mediator (matches .NET Program.cs configuration)
    configure_mediator()

    logger.log_with_context("Mediator pattern initialized", "info")


async def cleanup_dependency_injection() -> None:
    """Cleanup dependency injection container and associated resources."""
    logger = BaseLogger("initialization")
    logger.log_with_context("Cleaning up dependency injection container", "info")

    global _app_container
    if _app_container:
        try:
            # Unwire the container to release any wired dependencies
            _app_container.unwire()
            logger.log_with_context("Container unwired successfully", "info")

            # Clear any cached instances in providers
            for provider_name, provider in _app_container.providers.items():
                if hasattr(provider, "reset"):
                    provider.reset()
                    logger.log_debug_with_context(f"Reset provider: {provider_name}")

            # Clear the global container reference
            _app_container = None
            logger.log_with_context(
                "Dependency injection container cleanup completed", "info"
            )

        except Exception as e:
            logger.log_error_with_context(
                "Error during container cleanup",
                error=e,
                context={"container_available": _app_container is not None},
            )
            # Still clear the reference even if cleanup fails
            _app_container = None
    else:
        logger.log_with_context("No container to cleanup", "info")

    # Cleanup database resources
    try:
        from app.core.database.session import close_db_engine

        await close_db_engine()
        logger.log_with_context("Database engine closed successfully", "info")
    except Exception as e:
        logger.log_error_with_context("Error during database cleanup", error=e)


async def shutdown_logging() -> None:
    """Shutdown logging and flush remaining events."""
    logger = BaseLogger("initialization")
    logger.log_with_context("Shutting down logging system", "info")
    
    # Shutdown async CLEF dispatcher
    try:
        from app.core.logging.clef_dispatcher import shutdown_dispatcher
        
        await shutdown_dispatcher()
        logger.log_with_context("Async CLEF dispatcher shutdown completed", "info")
    except Exception as e:
        logger.log_error_with_context(
            "Error during CLEF dispatcher shutdown",
            error=e,
        )
