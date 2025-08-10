"""Comprehensive tests for the core lifecycle management system."""

import asyncio
import signal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI

from eshop.core.lifecycle.manager import (
    LifecycleManager,
    lifecycle_manager,
    register_shutdown_callback,
    register_startup_callback,
    set_shutdown_timeout,
)


class TestLifecycleManager:
    """Test the LifecycleManager class."""

    def test_lifecycle_manager_initialization(self):
        """Test LifecycleManager initialization."""
        manager = LifecycleManager()
        assert manager.startup_callbacks == []
        assert manager.shutdown_callbacks == []
        assert manager.is_shutting_down is False
        assert manager.shutdown_timeout == 30.0
        assert manager._shutdown_event is None

    def test_add_startup_callback(self):
        """Test adding startup callbacks."""
        manager = LifecycleManager()
        callback = AsyncMock()
        callback.__name__ = "test_callback"

        manager.add_startup_callback(callback)
        assert len(manager.startup_callbacks) == 1
        assert manager.startup_callbacks[0] == callback

    def test_add_shutdown_callback(self):
        """Test adding shutdown callbacks."""
        manager = LifecycleManager()
        callback = AsyncMock()
        callback.__name__ = "test_callback"

        manager.add_shutdown_callback(callback)
        assert len(manager.shutdown_callbacks) == 1
        assert manager.shutdown_callbacks[0] == callback

    def test_set_shutdown_timeout(self):
        """Test setting shutdown timeout."""
        manager = LifecycleManager()
        manager.set_shutdown_timeout(60.0)
        assert manager.shutdown_timeout == 60.0

    @pytest.mark.asyncio
    async def test_startup_success(self):
        """Test successful startup execution."""
        manager = LifecycleManager()
        callback1 = AsyncMock()
        callback1.__name__ = "callback1"
        callback2 = AsyncMock()
        callback2.__name__ = "callback2"

        manager.add_startup_callback(callback1)
        manager.add_startup_callback(callback2)

        await manager.startup()

        callback1.assert_called_once()
        callback2.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_failure(self):
        """Test startup failure handling."""
        manager = LifecycleManager()
        callback = AsyncMock()
        callback.__name__ = "failing_callback"
        callback.side_effect = Exception("Startup failed")

        manager.add_startup_callback(callback)

        with pytest.raises(
            RuntimeError, match="Startup failed in callback failing_callback"
        ):
            await manager.startup()

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """Test successful shutdown execution."""
        manager = LifecycleManager()
        callback1 = AsyncMock()
        callback1.__name__ = "callback1"
        callback2 = AsyncMock()
        callback2.__name__ = "callback2"

        manager.add_shutdown_callback(callback1)
        manager.add_shutdown_callback(callback2)

        await manager.shutdown()

        # Shutdown callbacks should be executed in reverse order
        callback2.assert_called_once()
        callback1.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_timeout(self):
        """Test shutdown timeout handling."""
        manager = LifecycleManager()
        manager.set_shutdown_timeout(0.1)  # Very short timeout

        async def slow_callback():
            await asyncio.sleep(1.0)  # Longer than timeout

        callback = AsyncMock(side_effect=slow_callback)
        callback.__name__ = "slow_callback"

        manager.add_shutdown_callback(callback)

        await manager.shutdown()

        # The callback should be called but may be cancelled due to timeout
        assert callback.called

    @pytest.mark.asyncio
    async def test_shutdown_duplicate_call(self):
        """Test duplicate shutdown call handling."""
        manager = LifecycleManager()
        callback = AsyncMock()
        callback.__name__ = "test_callback"

        manager.add_shutdown_callback(callback)

        # First shutdown call
        await manager.shutdown()
        assert manager.is_shutting_down is True

        # Second shutdown call should be ignored
        await manager.shutdown()
        # Should not raise any exception

    @pytest.mark.asyncio
    async def test_shutdown_callback_failure(self):
        """Test shutdown callback failure handling."""
        manager = LifecycleManager()
        callback = AsyncMock()
        callback.__name__ = "failing_callback"
        callback.side_effect = Exception("Shutdown failed")

        manager.add_shutdown_callback(callback)

        # Should not raise exception, just log error
        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_execute_shutdown_tasks(self):
        """Test internal shutdown task execution."""
        manager = LifecycleManager()
        callback1 = AsyncMock()
        callback1.__name__ = "callback1"
        callback2 = AsyncMock()
        callback2.__name__ = "callback2"

        manager.add_shutdown_callback(callback1)
        manager.add_shutdown_callback(callback2)

        await manager.shutdown()

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_setup_signal_handlers_windows(self):
        """Test signal handler setup on Windows."""
        with patch("sys.platform", "win32"):
            manager = LifecycleManager()
            manager.setup_signal_handlers()
            # Should not register handlers on Windows

    @patch("signal.signal")
    def test_setup_signal_handlers_unix(self, mock_signal):
        """Test signal handler setup on Unix."""
        with patch("sys.platform", "linux"):
            manager = LifecycleManager()
            manager.setup_signal_handlers()

            # Should register handlers for SIGTERM and SIGINT
            assert mock_signal.call_count == 2
            calls = [call[0][0] for call in mock_signal.call_args_list]
            assert signal.SIGTERM in calls
            assert signal.SIGINT in calls

    @pytest.mark.asyncio
    async def test_lifespan_context_success(self):
        """Test successful lifespan context execution."""
        manager = LifecycleManager()
        app = FastAPI()

        startup_callback = AsyncMock()
        startup_callback.__name__ = "startup"
        manager.add_startup_callback(startup_callback)

        shutdown_callback = AsyncMock()
        shutdown_callback.__name__ = "shutdown"
        manager.add_shutdown_callback(shutdown_callback)

        async with manager.lifespan_context(app):
            # Application should be running
            pass

        startup_callback.assert_called_once()
        shutdown_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_context_startup_failure(self):
        """Test lifespan context with startup failure."""
        manager = LifecycleManager()
        app = FastAPI()

        startup_callback = AsyncMock()
        startup_callback.__name__ = "failing_startup"
        startup_callback.side_effect = Exception("Startup failed")
        manager.add_startup_callback(startup_callback)

        with pytest.raises(Exception, match="Startup failed"):
            async with manager.lifespan_context(app):
                pass

    @pytest.mark.asyncio
    async def test_wait_for_shutdown_signal(self):
        """Test shutdown signal waiting."""
        manager = LifecycleManager()
        manager.setup_signal_handlers()

        if manager._shutdown_event:
            # Test that the method can be called
            task = asyncio.create_task(manager._wait_for_shutdown_signal())

            # Cancel the task to avoid hanging
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task


class TestGlobalLifecycleManager:
    """Test the global lifecycle manager functions."""

    def test_register_startup_callback(self):
        """Test global startup callback registration."""
        callback = AsyncMock()
        callback.__name__ = "global_startup"

        register_startup_callback(callback)
        assert callback in lifecycle_manager.startup_callbacks

    def test_register_shutdown_callback(self):
        """Test global shutdown callback registration."""
        callback = AsyncMock()
        callback.__name__ = "global_shutdown"

        register_shutdown_callback(callback)
        assert callback in lifecycle_manager.shutdown_callbacks

    def test_set_shutdown_timeout(self):
        """Test global shutdown timeout setting."""
        original_timeout = lifecycle_manager.shutdown_timeout
        set_shutdown_timeout(45.0)
        assert lifecycle_manager.shutdown_timeout == 45.0

        # Restore original timeout
        set_shutdown_timeout(original_timeout)


class TestLifecycleManagerIntegration:
    """Integration tests for lifecycle manager."""

    @pytest.mark.asyncio
    async def test_full_lifecycle_flow(self):
        """Test complete lifecycle flow."""
        manager = LifecycleManager()
        app = FastAPI()

        startup_order = []
        shutdown_order = []

        async def startup1():
            startup_order.append("startup1")
            await asyncio.sleep(0.01)

        async def startup2():
            startup_order.append("startup2")
            await asyncio.sleep(0.01)

        async def shutdown1():
            shutdown_order.append("shutdown1")
            await asyncio.sleep(0.01)

        async def shutdown2():
            shutdown_order.append("shutdown2")
            await asyncio.sleep(0.01)

        manager.add_startup_callback(startup1)
        manager.add_startup_callback(startup2)
        manager.add_shutdown_callback(shutdown1)
        manager.add_shutdown_callback(shutdown2)

        async with manager.lifespan_context(app):
            # Application is running
            pass

        # Verify startup order (FIFO)
        assert startup_order == ["startup1", "startup2"]

        # Verify shutdown order (LIFO)
        assert shutdown_order == ["shutdown2", "shutdown1"]

    @pytest.mark.asyncio
    async def test_lifecycle_manager_with_fastapi_app(self):
        """Test lifecycle manager integration with FastAPI app."""
        manager = LifecycleManager()

        # Create a simple FastAPI app
        app = FastAPI()

        # Add some test callbacks
        startup_called = False
        shutdown_called = False

        async def test_startup():
            nonlocal startup_called
            startup_called = True

        async def test_shutdown():
            nonlocal shutdown_called
            shutdown_called = True

        manager.add_startup_callback(test_startup)
        manager.add_shutdown_callback(test_shutdown)

        # Use the lifespan context
        async with manager.lifespan_context(app):
            assert startup_called is True
            assert shutdown_called is False

        assert shutdown_called is True

    @pytest.mark.asyncio
    async def test_lifecycle_manager_error_handling(self):
        """Test error handling in lifecycle manager."""
        manager = LifecycleManager()
        app = FastAPI()

        # Add a callback that raises an exception
        async def error_callback():
            raise ValueError("Test error")

        manager.add_startup_callback(error_callback)

        # Should raise the exception
        with pytest.raises(
            RuntimeError, match="Startup failed in callback error_callback"
        ):
            async with manager.lifespan_context(app):
                pass

    @pytest.mark.asyncio
    async def test_lifecycle_manager_timeout_behavior(self):
        """Test timeout behavior in lifecycle manager."""
        manager = LifecycleManager()
        manager.set_shutdown_timeout(0.1)  # Very short timeout

        async def slow_shutdown():
            await asyncio.sleep(1.0)  # Longer than timeout

        manager.add_shutdown_callback(slow_shutdown)

        # Should not hang indefinitely
        start_time = asyncio.get_event_loop().time()
        await manager.shutdown()
        end_time = asyncio.get_event_loop().time()

        # Should complete within reasonable time (less than 1 second)
        assert end_time - start_time < 1.0
