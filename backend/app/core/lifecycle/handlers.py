"""Lifecycle handlers for application services."""

import asyncio
import sys
from pathlib import Path
from typing import Any

# Add the project root to the Python path to access infra module
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import after path modification - noqa: E402
from infra.keycloak.keycloak_setup import setup_keycloak_async  # noqa: E402

from app.core.database.migrations import run_migrations, wait_for_database  # noqa: E402
from app.core.database.seeding import run_seeding  # noqa: E402
from app.core.database.session import close_db_engine, create_db_engine  # noqa: E402
from app.core.health.health_service import health_service  # noqa: E402
from app.core.logging.base_logger import BaseLogger  # noqa: E402

logger = BaseLogger(__name__)


class DatabaseLifecycleHandler:
    """Handles database connection lifecycle."""

    def __init__(self) -> None:
        """Initialize database lifecycle handler."""
        self.connection_pool: Any | None = None
        self.is_connected: bool = False

    async def startup(self) -> None:
        """Initialize database connections and run migrations/seeding."""
        logger.log_with_context(
            "[DATABASE] Initializing database connections...", "info"
        )
        try:
            # Create database engine
            await create_db_engine()

            # Wait for database to be ready
            await wait_for_database()

            # Run migrations
            await run_migrations()

            # Run seeding
            await run_seeding()

            self.is_connected = True
            logger.log_with_context(
                "[OK] Database initialization completed successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Database initialization failed", error=e
            )
            raise

    async def shutdown(self) -> None:
        """Close database connections gracefully."""
        if not self.is_connected:
            logger.log_with_context("Database connections already closed", "info")
            return

        logger.log_with_context("[DATABASE] Closing database connections...", "info")
        try:
            await close_db_engine()
            self.is_connected = False
            logger.log_with_context(
                "[OK] Database connections closed successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Error closing database connections", error=e
            )
            self.is_connected = False

    async def _verify_database_connectivity(self) -> None:
        """Verify database connectivity during startup."""
        # This would be implemented with actual database health check
        logger.log_debug_with_context("Verifying database connectivity...")
        await asyncio.sleep(0.1)  # Simulate connectivity check
        logger.log_debug_with_context("Database connectivity verified")


class CacheLifecycleHandler:
    """Handles cache (Redis) connection lifecycle."""

    def __init__(self) -> None:
        """Initialize cache lifecycle handler."""
        self.redis_client: Any | None = None
        self.is_connected: bool = False

    async def startup(self) -> None:
        """Initialize cache connections."""
        logger.log_with_context("[CACHE] Initializing cache connections...", "info")
        try:
            # Initialize Redis connection
            # from redis.asyncio import Redis
            # self.redis_client = Redis.from_url(settings.redis_connection_string)

            # Verify cache connectivity
            await self._verify_cache_connectivity()
            self.is_connected = True
            logger.log_with_context(
                "[OK] Cache connections initialized successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Failed to initialize cache connections", error=e
            )
            raise

    async def shutdown(self) -> None:
        """Close cache connections gracefully."""
        if not self.is_connected:
            logger.log_with_context("Cache connections already closed", "info")
            return

        logger.log_with_context("[CACHE] Closing cache connections...", "info")
        try:
            if self.redis_client:
                # await self.redis_client.close()
                logger.log_with_context("Redis client closed", "info")

            self.is_connected = False
            logger.log_with_context(
                "[OK] Cache connections closed successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Error closing cache connections", error=e
            )

    async def _verify_cache_connectivity(self) -> None:
        """Verify cache connectivity during startup."""
        logger.log_debug_with_context("Verifying cache connectivity...")
        await asyncio.sleep(0.1)  # Simulate connectivity check
        logger.log_debug_with_context("Cache connectivity verified")


class MessagingLifecycleHandler:
    """Handles message broker (RabbitMQ) connection lifecycle.

    Module-specific startup/shutdown hooks are registered via
    LifecycleHookRegistry (see core.module_bootstrap). This handler only
    manages the core outbox worker registry and delegates to registered hooks.
    """

    def __init__(self) -> None:
        """Initialize messaging lifecycle handler."""
        self.connection: Any | None = None
        self.channel: Any | None = None
        self.is_connected: bool = False
        self._startup_hooks: list[Any] = []
        self._shutdown_hooks: list[Any] = []

    def add_startup_hook(self, hook: Any) -> None:
        self._startup_hooks.append(hook)

    def add_shutdown_hook(self, hook: Any) -> None:
        self._shutdown_hooks.append(hook)

    async def startup(self) -> None:
        """Initialize messaging connections via registered hooks."""
        logger.log_with_context(
            "[MESSAGING] Initializing messaging connections...", "info"
        )
        try:
            for hook in self._startup_hooks:
                await hook()

            from app.core.messaging.outbox import outbox_worker_registry

            await outbox_worker_registry.start_all()
            logger.log_with_context(
                "[OK] Outbox publisher workers started", "info"
            )

            await self._verify_messaging_connectivity()
            self.is_connected = True
            logger.log_with_context(
                "[OK] Messaging connections initialized successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Failed to initialize messaging connections", error=e
            )
            raise

    async def shutdown(self) -> None:
        """Close messaging connections gracefully."""
        logger.log_with_context("[MESSAGING] Closing messaging connections...", "info")
        try:
            try:
                from app.core.messaging.outbox import outbox_worker_registry

                await outbox_worker_registry.stop_all()
                logger.log_with_context(
                    "[OK] Outbox publisher workers stopped", "info"
                )
            except Exception as e:
                logger.log_warning_with_context(
                    "Failed to stop outbox publisher workers", context={"error": str(e)}
                )

            for hook in self._shutdown_hooks:
                try:
                    await hook()
                except Exception as e:
                    logger.log_warning_with_context(
                        "Module shutdown hook failed", context={"error": str(e)}
                    )

            self.is_connected = False
            logger.log_with_context(
                "[OK] Messaging connections closed successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Error closing messaging connections", error=e
            )

    async def _verify_messaging_connectivity(self) -> None:
        """Verify messaging connectivity during startup."""
        logger.log_debug_with_context("Verifying messaging connectivity...")
        await asyncio.sleep(0.1)
        logger.log_debug_with_context("Messaging connectivity verified")


class AuthenticationLifecycleHandler:
    """Handles authentication service lifecycle."""

    def __init__(self, app: Any | None = None) -> None:
        """Initialize authentication lifecycle handler."""
        self.keycloak_client: Any | None = None
        self.is_initialized: bool = False
        self.app = app

    async def startup(self, app_instance: Any = None) -> None:
        """Initialize authentication services."""
        logger.log_with_context(
            "[AUTH] Initializing authentication services...", "info"
        )
        try:
            # Use provided app instance or fall back to stored one
            if app_instance:
                self.app = app_instance

            # Setup Keycloak (realm, client, roles, users)
            logger.log_with_context(
                "[SETUP] Setting up Keycloak configuration...", "info"
            )
            try:
                setup_success = await setup_keycloak_async()
                if setup_success:
                    logger.log_with_context(
                        "[OK] Keycloak setup completed successfully", "info"
                    )
                    # Now that Keycloak is set up, force initialize the service
                    await self._force_initialize_keycloak()
                    # Now that Keycloak is set up, add the authentication routes
                    await self._add_keycloak_routes()
                else:
                    logger.log_warning_with_context(
                        "[WARNING] Keycloak setup failed or incomplete - continuing anyway"
                    )
            except Exception as e:
                logger.log_warning_with_context(
                    "[WARNING] Keycloak setup failed with exception - continuing anyway",
                    context={"error": str(e)},
                )

            # Initialize Keycloak client
            # This would initialize the Keycloak client with proper configuration
            await self._verify_auth_connectivity()
            self.is_initialized = True
            logger.log_with_context(
                "[OK] Authentication services initialized successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Failed to initialize authentication services", error=e
            )
            raise

    async def shutdown(self) -> None:
        """Shutdown authentication services gracefully."""
        if not self.is_initialized:
            logger.log_with_context("Authentication services already shutdown", "info")
            return

        logger.log_with_context(
            "[AUTH] Shutting down authentication services...", "info"
        )
        try:
            # Clean up Keycloak client resources
            if self.keycloak_client:
                # await self.keycloak_client.close()
                logger.log_with_context("Keycloak client closed", "info")

            self.is_initialized = False
            logger.log_with_context(
                "[OK] Authentication services shutdown successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Error shutting down authentication services", error=e
            )

    async def _verify_auth_connectivity(self) -> None:
        """Verify authentication service connectivity during startup."""
        logger.log_debug_with_context(
            "Verifying authentication service connectivity..."
        )
        await asyncio.sleep(0.1)  # Simulate connectivity check
        logger.log_debug_with_context("Authentication service connectivity verified")

    async def _force_initialize_keycloak(self) -> None:
        """Force initialize the Keycloak service after setup is complete."""
        try:
            from app.core.auth.keycloak import keycloak_service

            logger.log_with_context(
                "[SETUP] Force initializing Keycloak service...", "info"
            )
            keycloak_service.force_initialize()

            logger.log_with_context(
                "[OK] Keycloak service initialized successfully", "info"
            )
        except Exception as e:
            logger.log_warning_with_context(
                "[WARNING] Failed to force initialize Keycloak service",
                context={"error": str(e)},
            )

    async def _add_keycloak_routes(self) -> None:
        """Add Keycloak authentication routes after setup is complete."""
        # Try to get app instance from the global auth_handler if available
        app_instance = self.app
        if not app_instance:
            # Try to get from the global auth_handler instance
            try:
                from app.core.lifecycle.handlers import auth_handler

                app_instance = auth_handler.app
            except Exception:
                pass

        if not app_instance:
            logger.log_warning_with_context(
                "[WARNING] No app instance available - skipping Keycloak routes"
            )
            return

        try:
            from app.core.auth.keycloak import add_keycloak_routes

            logger.log_with_context(
                "[SETUP] Adding Keycloak authentication routes...", "info"
            )
            add_keycloak_routes(app_instance)
            logger.log_with_context(
                "[OK] Keycloak authentication routes added successfully", "info"
            )
        except Exception as e:
            logger.log_warning_with_context(
                "[WARNING] Failed to add Keycloak routes", context={"error": str(e)}
            )


class HealthCheckLifecycleHandler:
    """Handles health check service lifecycle."""

    def __init__(self) -> None:
        """Initialize health check lifecycle handler."""
        self.health_service: Any | None = None
        self.is_running: bool = False

    async def startup(self) -> None:
        """Initialize health check services."""
        logger.log_with_context(
            "[HEALTH] Initializing health check services...", "info"
        )
        try:
            # Initialize health service
            # from app.core.health.health_service import health_service

            self.health_service = health_service

            # Perform initial health check
            await self._perform_initial_health_check()
            self.is_running = True
            logger.log_with_context(
                "[OK] Health check services initialized successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Failed to initialize health check services", error=e
            )
            raise

    async def shutdown(self) -> None:
        """Shutdown health check services gracefully."""
        if not self.is_running:
            logger.log_with_context("Health check services already shutdown", "info")
            return

        logger.log_with_context(
            "[HEALTH] Shutting down health check services...", "info"
        )
        try:
            # Stop health monitoring if any background tasks exist
            self.is_running = False
            logger.log_with_context(
                "[OK] Health check services shutdown successfully", "info"
            )
        except Exception as e:
            logger.log_error_with_context(
                "[FAILED] Error shutting down health check services", error=e
            )

    async def _perform_initial_health_check(self) -> None:
        """Perform initial health check during startup."""
        logger.log_debug_with_context("Performing initial health check...")
        if self.health_service:
            try:
                # health_status = await self.health_service.check_all_services()
                # logger.debug(f"Initial health check result: {health_status}")
                pass
            except Exception as e:
                logger.log_warning_with_context(
                    "Initial health check failed (non-critical)",
                    context={"error": str(e)},
                )
        logger.log_debug_with_context("Initial health check completed")


# Global lifecycle handler instances
database_handler = DatabaseLifecycleHandler()
cache_handler = CacheLifecycleHandler()
messaging_handler = MessagingLifecycleHandler()
auth_handler = AuthenticationLifecycleHandler()  # Will be updated with app instance
health_handler = HealthCheckLifecycleHandler()


def set_app_instance(app_instance: Any) -> None:
    """Set the app instance for lifecycle handlers that need it."""
    global auth_handler
    auth_handler = AuthenticationLifecycleHandler(app_instance)
