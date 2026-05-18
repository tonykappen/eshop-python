"""Tests for lifecycle handlers."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.lifecycle.handlers import (AuthenticationLifecycleHandler,
                                         CacheLifecycleHandler,
                                         DatabaseLifecycleHandler,
                                         HealthCheckLifecycleHandler,
                                         MessagingLifecycleHandler,
                                         auth_handler, cache_handler,
                                         database_handler, health_handler,
                                         messaging_handler)


class TestDatabaseLifecycleHandler:
    """Test database lifecycle handler."""

    def test_database_handler_initialization(self) -> None:
        """Test database handler initialization."""
        handler = DatabaseLifecycleHandler()
        assert handler.connection_pool is None
        assert handler.is_connected is False

    @patch("app.core.lifecycle.handlers.create_db_engine")
    @patch("app.core.lifecycle.handlers.wait_for_database")
    @patch("app.core.lifecycle.handlers.run_migrations")
    @patch("app.core.lifecycle.handlers.run_seeding")
    async def test_startup_success(
        self,
        mock_run_seeding: AsyncMock,
        mock_run_migrations: AsyncMock,
        mock_wait_for_database: AsyncMock,
        mock_create_db_engine: AsyncMock,
    ) -> None:
        """Test successful database startup."""
        handler = DatabaseLifecycleHandler()

        await handler.startup()

        mock_create_db_engine.assert_called_once()
        mock_wait_for_database.assert_called_once()
        mock_run_migrations.assert_called_once()
        mock_run_seeding.assert_called_once()
        assert handler.is_connected is True

    @patch("app.core.lifecycle.handlers.create_db_engine")
    async def test_startup_failure(self, mock_create_db_engine: AsyncMock) -> None:
        """Test database startup failure."""
        mock_create_db_engine.side_effect = Exception("Database connection failed")
        handler = DatabaseLifecycleHandler()

        with pytest.raises(Exception, match="Database connection failed"):
            await handler.startup()

        assert handler.is_connected is False

    @patch("app.core.lifecycle.handlers.close_db_engine")
    async def test_shutdown_success(self, mock_close_db_engine: AsyncMock) -> None:
        """Test successful database shutdown."""
        handler = DatabaseLifecycleHandler()
        handler.is_connected = True

        await handler.shutdown()

        mock_close_db_engine.assert_called_once()
        assert handler.is_connected is False

    @patch("app.core.lifecycle.handlers.close_db_engine")
    async def test_shutdown_failure(self, mock_close_db_engine: AsyncMock) -> None:
        """Test database shutdown failure."""
        mock_close_db_engine.side_effect = Exception("Close failed")
        handler = DatabaseLifecycleHandler()
        handler.is_connected = True

        # Should not raise exception
        await handler.shutdown()

        mock_close_db_engine.assert_called_once()
        assert handler.is_connected is False

    async def test_shutdown_already_closed(self) -> None:
        """Test shutdown when already closed."""
        handler = DatabaseLifecycleHandler()
        handler.is_connected = False

        await handler.shutdown()

        assert handler.is_connected is False

    async def test_verify_database_connectivity(self) -> None:
        """Test database connectivity verification."""
        handler = DatabaseLifecycleHandler()

        start_time = asyncio.get_event_loop().time()
        await handler._verify_database_connectivity()
        end_time = asyncio.get_event_loop().time()

        # Should take at least 0.1 seconds due to sleep
        assert end_time - start_time >= 0.1


class TestCacheLifecycleHandler:
    """Test cache lifecycle handler."""

    def test_cache_handler_initialization(self) -> None:
        """Test cache handler initialization."""
        handler = CacheLifecycleHandler()
        assert handler.redis_client is None
        assert handler.is_connected is False

    async def test_startup_success(self) -> None:
        """Test successful cache startup."""
        handler = CacheLifecycleHandler()

        await handler.startup()

        assert handler.is_connected is True

    async def test_startup_failure(self) -> None:
        """Test cache startup failure."""
        handler = CacheLifecycleHandler()

        # Mock the connectivity check to fail
        with patch.object(
            handler, "_verify_cache_connectivity", side_effect=Exception("Cache failed")
        ):
            with pytest.raises(Exception, match="Cache failed"):
                await handler.startup()

            assert handler.is_connected is False

    async def test_shutdown_success(self) -> None:
        """Test successful cache shutdown."""
        handler = CacheLifecycleHandler()
        handler.is_connected = True
        handler.redis_client = MagicMock()

        await handler.shutdown()

        assert handler.is_connected is False

    async def test_shutdown_failure(self) -> None:
        """Test cache shutdown failure."""
        handler = CacheLifecycleHandler()
        handler.is_connected = True
        handler.redis_client = MagicMock()

        # Mock redis client close to fail
        handler.redis_client.close = MagicMock(side_effect=Exception("Close failed"))

        # Should not raise exception
        await handler.shutdown()

        assert handler.is_connected is False

    async def test_shutdown_already_closed(self) -> None:
        """Test shutdown when already closed."""
        handler = CacheLifecycleHandler()
        handler.is_connected = False

        await handler.shutdown()

        assert handler.is_connected is False

    async def test_verify_cache_connectivity(self) -> None:
        """Test cache connectivity verification."""
        handler = CacheLifecycleHandler()

        start_time = asyncio.get_event_loop().time()
        await handler._verify_cache_connectivity()
        end_time = asyncio.get_event_loop().time()

        # Should take at least 0.1 seconds due to sleep
        assert end_time - start_time >= 0.1


class TestMessagingLifecycleHandler:
    """Test messaging lifecycle handler."""

    def test_messaging_handler_initialization(self) -> None:
        """Test messaging handler initialization."""
        handler = MessagingLifecycleHandler()
        assert handler.connection is None
        assert handler.channel is None
        assert handler.is_connected is False

    async def test_startup_success(self) -> None:
        """Test successful messaging startup."""
        handler = MessagingLifecycleHandler()

        await handler.startup()

        assert handler.is_connected is True

    async def test_startup_failure(self) -> None:
        """Test messaging startup failure."""
        handler = MessagingLifecycleHandler()

        # Mock the connectivity check to fail
        with patch.object(
            handler,
            "_verify_messaging_connectivity",
            side_effect=Exception("Messaging failed"),
        ):
            with pytest.raises(Exception, match="Messaging failed"):
                await handler.startup()

            assert handler.is_connected is False

    async def test_shutdown_success(self) -> None:
        """Test successful messaging shutdown."""
        handler = MessagingLifecycleHandler()
        handler.is_connected = True
        handler.channel = MagicMock()
        handler.connection = MagicMock()

        await handler.shutdown()

        assert handler.is_connected is False

    async def test_shutdown_failure(self) -> None:
        """Test messaging shutdown failure."""
        handler = MessagingLifecycleHandler()
        handler.is_connected = True
        handler.channel = MagicMock()
        handler.connection = MagicMock()

        # Mock channel close to fail
        handler.channel.close = MagicMock(side_effect=Exception("Close failed"))

        # Should not raise exception
        await handler.shutdown()

        assert handler.is_connected is False

    async def test_shutdown_already_closed(self) -> None:
        """Test shutdown when already closed."""
        handler = MessagingLifecycleHandler()
        handler.is_connected = False

        await handler.shutdown()

        assert handler.is_connected is False

    async def test_verify_messaging_connectivity(self) -> None:
        """Test messaging connectivity verification."""
        handler = MessagingLifecycleHandler()

        start_time = asyncio.get_event_loop().time()
        await handler._verify_messaging_connectivity()
        end_time = asyncio.get_event_loop().time()

        # Should take at least 0.1 seconds due to sleep
        assert end_time - start_time >= 0.1


class TestAuthenticationLifecycleHandler:
    """Test authentication lifecycle handler."""

    def test_auth_handler_initialization(self) -> None:
        """Test auth handler initialization."""
        handler = AuthenticationLifecycleHandler()
        assert handler.keycloak_client is None
        assert handler.is_initialized is False

    async def test_startup_success(self) -> None:
        """Test successful auth startup."""
        handler = AuthenticationLifecycleHandler()

        await handler.startup()

        assert handler.is_initialized is True

    async def test_startup_failure(self) -> None:
        """Test auth startup failure."""
        handler = AuthenticationLifecycleHandler()

        # Mock the connectivity check to fail
        with patch.object(
            handler, "_verify_auth_connectivity", side_effect=Exception("Auth failed")
        ):
            with pytest.raises(Exception, match="Auth failed"):
                await handler.startup()

            assert handler.is_initialized is False

    async def test_shutdown_success(self) -> None:
        """Test successful auth shutdown."""
        handler = AuthenticationLifecycleHandler()
        handler.is_initialized = True
        handler.keycloak_client = MagicMock()

        await handler.shutdown()

        assert handler.is_initialized is False

    async def test_shutdown_failure(self) -> None:
        """Test auth shutdown failure."""
        handler = AuthenticationLifecycleHandler()
        handler.is_initialized = True
        handler.keycloak_client = MagicMock()

        # Mock keycloak client close to fail
        handler.keycloak_client.close = MagicMock(side_effect=Exception("Close failed"))

        # Should not raise exception
        await handler.shutdown()

        assert handler.is_initialized is False

    async def test_shutdown_already_shutdown(self) -> None:
        """Test shutdown when already shutdown."""
        handler = AuthenticationLifecycleHandler()
        handler.is_initialized = False

        await handler.shutdown()

        assert handler.is_initialized is False

    async def test_verify_auth_connectivity(self) -> None:
        """Test auth connectivity verification."""
        handler = AuthenticationLifecycleHandler()

        start_time = asyncio.get_event_loop().time()
        await handler._verify_auth_connectivity()
        end_time = asyncio.get_event_loop().time()

        # Should take at least 0.1 seconds due to sleep
        assert end_time - start_time >= 0.1


class TestHealthCheckLifecycleHandler:
    """Test health check lifecycle handler."""

    def test_health_handler_initialization(self) -> None:
        """Test health handler initialization."""
        handler = HealthCheckLifecycleHandler()
        assert handler.health_service is None
        assert handler.is_running is False

    @patch("app.core.lifecycle.handlers.health_service")
    async def test_startup_success(self, mock_health_service: MagicMock) -> None:
        """Test successful health startup."""
        handler = HealthCheckLifecycleHandler()

        await handler.startup()

        assert handler.health_service == mock_health_service
        assert handler.is_running is True

    async def test_startup_failure(self) -> None:
        """Test health startup failure."""
        handler = HealthCheckLifecycleHandler()

        # Mock the health check to fail
        with patch.object(
            handler,
            "_perform_initial_health_check",
            side_effect=Exception("Health failed"),
        ):
            with pytest.raises(Exception, match="Health failed"):
                await handler.startup()

            assert handler.is_running is False

    async def test_shutdown_success(self) -> None:
        """Test successful health shutdown."""
        handler = HealthCheckLifecycleHandler()
        handler.is_running = True

        await handler.shutdown()

        assert handler.is_running is False

    async def test_shutdown_failure(self) -> None:
        """Test health shutdown failure."""
        handler = HealthCheckLifecycleHandler()
        handler.is_running = True

        # Mock shutdown to fail
        with patch.object(
            handler,
            "_perform_initial_health_check",
            side_effect=Exception("Shutdown failed"),
        ):
            # Should not raise exception
            await handler.shutdown()

            assert handler.is_running is False

    async def test_shutdown_already_shutdown(self) -> None:
        """Test shutdown when already shutdown."""
        handler = HealthCheckLifecycleHandler()
        handler.is_running = False

        await handler.shutdown()

        assert handler.is_running is False

    async def test_perform_initial_health_check_success(self) -> None:
        """Test successful initial health check."""
        handler = HealthCheckLifecycleHandler()
        handler.health_service = MagicMock()

        await handler._perform_initial_health_check()

    async def test_perform_initial_health_check_failure(self) -> None:
        """Test initial health check failure."""
        handler = HealthCheckLifecycleHandler()
        handler.health_service = MagicMock()
        handler.health_service.check_all_services = AsyncMock(
            side_effect=Exception("Health check failed")
        )

        # Should not raise exception, just log warning
        await handler._perform_initial_health_check()

    async def test_perform_initial_health_check_no_service(self) -> None:
        """Test initial health check with no health service."""
        handler = HealthCheckLifecycleHandler()
        handler.health_service = None

        await handler._perform_initial_health_check()


class TestGlobalLifecycleHandlers:
    """Test global lifecycle handler instances."""

    def test_global_handlers_exist(self) -> None:
        """Test that global handlers are properly instantiated."""
        assert isinstance(database_handler, DatabaseLifecycleHandler)
        assert isinstance(cache_handler, CacheLifecycleHandler)
        assert isinstance(messaging_handler, MessagingLifecycleHandler)
        assert isinstance(auth_handler, AuthenticationLifecycleHandler)
        assert isinstance(health_handler, HealthCheckLifecycleHandler)

    def test_global_handlers_initial_state(self) -> None:
        """Test initial state of global handlers."""
        assert database_handler.is_connected is False
        assert cache_handler.is_connected is False
        assert messaging_handler.is_connected is False
        assert auth_handler.is_initialized is False
        assert health_handler.is_running is False


class TestLifecycleHandlersIntegration:
    """Integration tests for lifecycle handlers."""

    @patch("app.core.lifecycle.handlers.create_db_engine")
    @patch("app.core.lifecycle.handlers.wait_for_database")
    @patch("app.core.lifecycle.handlers.run_migrations")
    @patch("app.core.lifecycle.handlers.run_seeding")
    @patch("app.core.lifecycle.handlers.health_service")
    async def test_full_lifecycle_flow(
        self,
        mock_health_service: MagicMock,  # noqa: ARG002
        mock_run_seeding: AsyncMock,  # noqa: ARG002
        mock_run_migrations: AsyncMock,  # noqa: ARG002
        mock_wait_for_database: AsyncMock,  # noqa: ARG002
        mock_create_db_engine: AsyncMock,  # noqa: ARG002
    ) -> None:
        """Test complete lifecycle flow for all handlers."""
        # Test database handler
        await database_handler.startup()
        assert database_handler.is_connected is True

        # Test cache handler
        await cache_handler.startup()
        assert cache_handler.is_connected is True

        # Test messaging handler
        await messaging_handler.startup()
        assert messaging_handler.is_connected is True

        # Test auth handler
        await auth_handler.startup()
        assert auth_handler.is_initialized is True

        # Test health handler
        await health_handler.startup()
        assert health_handler.is_running is True

        # Test shutdown in reverse order
        await health_handler.shutdown()
        assert health_handler.is_running is False

        await auth_handler.shutdown()
        assert auth_handler.is_initialized is False

        await messaging_handler.shutdown()
        assert messaging_handler.is_connected is False

        await cache_handler.shutdown()
        assert cache_handler.is_connected is False

        await database_handler.shutdown()
        assert database_handler.is_connected is False

    async def test_concurrent_startup(self) -> None:
        """Test concurrent startup of multiple handlers."""
        handlers = [
            database_handler,
            cache_handler,
            messaging_handler,
            auth_handler,
            health_handler,
        ]

        # Start all handlers concurrently
        with (
            patch("app.core.lifecycle.handlers.create_db_engine"),
            patch("app.core.lifecycle.handlers.wait_for_database"),
            patch("app.core.lifecycle.handlers.run_migrations"),
            patch("app.core.lifecycle.handlers.run_seeding"),
            patch("app.core.lifecycle.handlers.health_service"),
        ):
            await asyncio.gather(*[handler.startup() for handler in handlers])

            # Verify all handlers are started
            assert database_handler.is_connected is True
            assert cache_handler.is_connected is True
            assert messaging_handler.is_connected is True
            assert auth_handler.is_initialized is True
            assert health_handler.is_running is True

    async def test_error_recovery(self) -> None:
        """Test error recovery in lifecycle handlers."""
        # Test that one handler failure doesn't affect others
        with patch.object(
            database_handler, "startup", side_effect=Exception("DB failed")
        ):
            with pytest.raises(Exception, match="DB failed"):
                await database_handler.startup()

            # Other handlers should still work
            await cache_handler.startup()
            assert cache_handler.is_connected is True

            await cache_handler.shutdown()
            assert cache_handler.is_connected is False
