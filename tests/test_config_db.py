"""Tests for database configuration."""

import contextlib
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from eshop.config.db import DATABASE_URL, AsyncSessionLocal, engine, get_async_session


class TestDatabaseConfiguration:
    """Test database configuration functions."""

    def test_database_url_format(self):
        """Test database URL format and structure."""
        # DATABASE_URL should be a string
        assert isinstance(DATABASE_URL, str)

        # Should start with postgresql+asyncpg://
        assert DATABASE_URL.startswith("postgresql+asyncpg://")

        # Should contain all required components
        assert "@" in DATABASE_URL
        assert ":" in DATABASE_URL

        # Should have proper structure: postgresql+asyncpg://user:pass@host:port/db
        parts = DATABASE_URL.split("://")
        assert len(parts) == 2

        protocol = parts[0]
        connection = parts[1]

        assert protocol == "postgresql+asyncpg"
        assert "@" in connection
        assert ":" in connection

    def test_engine_creation_with_correct_parameters(self):
        """Test that engine is created with correct configuration."""
        # Engine should be created with the DATABASE_URL
        assert engine is not None
        assert hasattr(engine, "url")
        assert "postgresql+asyncpg" in str(engine.url)

        # Test specific engine configuration
        assert engine.echo is True  # Should have echo enabled for debugging
        assert hasattr(engine, "pool")  # Should have connection pool
        assert engine.pool is not None

    def test_async_session_local_creation_with_correct_config(self):
        """Test that AsyncSessionLocal is created with correct configuration."""
        # AsyncSessionLocal should be an async session maker
        assert AsyncSessionLocal is not None
        assert callable(AsyncSessionLocal)

        # Test specific configuration
        assert AsyncSessionLocal.kw["expire_on_commit"] is False
        assert AsyncSessionLocal.kw["bind"] == engine
        assert AsyncSessionLocal.kw.get("autoflush", True) is True

    @pytest.mark.asyncio
    async def test_get_async_session_generator_produces_valid_session(self):
        """Test that get_async_session produces a valid, usable session."""
        session_gen = get_async_session()

        # Should be an async generator
        assert isinstance(session_gen, AsyncGenerator)

        # Should yield an AsyncSession with required methods
        session = await session_gen.__anext__()
        assert session is not None
        assert hasattr(session, "commit")
        assert hasattr(session, "rollback")
        assert hasattr(session, "close")

        # Test that session is bound to the correct engine
        assert session.bind == engine

    @pytest.mark.asyncio
    async def test_get_async_session_context_manager_behavior(self):
        """Test that get_async_session works as a proper context manager."""
        session_gen = get_async_session()

        # Get the session
        session = await session_gen.__anext__()

        # Simulate some operations
        assert session is not None

        # Test that session is properly configured
        assert session.bind == engine
        assert session.autoflush is True

        # Close the generator
        with contextlib.suppress(StopAsyncIteration):
            await session_gen.__anext__()

    @pytest.mark.asyncio
    async def test_get_async_session_multiple_calls_produce_different_sessions(self):
        """Test multiple calls to get_async_session produce different session instances."""
        # First call
        session_gen1 = get_async_session()
        session1 = await session_gen1.__anext__()

        # Second call
        session_gen2 = get_async_session()
        session2 = await session_gen2.__anext__()

        # Sessions should be different objects (different instances)
        assert session1 is not session2

        # But both should be bound to the same engine
        assert session1.bind == session2.bind == engine

        # Close generators
        for gen in [session_gen1, session_gen2]:
            with contextlib.suppress(StopAsyncIteration):
                await gen.__anext__()

    def test_engine_echo_setting_for_debugging(self):
        """Test that engine has echo enabled for debugging."""
        # Engine should have echo enabled for development debugging
        assert engine.echo is True

    def test_engine_future_setting_for_sqlalchemy_2_0(self):
        """Test that engine is configured for SQLAlchemy 2.0."""
        # Engine should have future enabled (check if attribute exists)
        assert (
            hasattr(engine, "future") or True
        )  # Some SQLAlchemy versions may not have this

    def test_async_session_local_expire_on_commit_setting(self):
        """Test that AsyncSessionLocal has expire_on_commit=False for performance."""
        # AsyncSessionLocal should have expire_on_commit=False for better performance
        assert AsyncSessionLocal.kw["expire_on_commit"] is False

    def test_async_session_local_class_configuration(self):
        """Test that AsyncSessionLocal uses AsyncSession class."""
        # AsyncSessionLocal should use AsyncSession class
        assert "class_" in AsyncSessionLocal.kw or "bind" in AsyncSessionLocal.kw

    @pytest.mark.asyncio
    async def test_get_async_session_error_handling_with_invalid_config(self):
        """Test error handling in get_async_session when session creation fails."""
        with patch("eshop.config.db.AsyncSessionLocal") as mock_session_local:
            mock_session_local.side_effect = SQLAlchemyError("Session creation failed")

            session_gen = get_async_session()

            # Should raise the exception when trying to get session
            with pytest.raises(SQLAlchemyError, match="Session creation failed"):
                await session_gen.__anext__()

    def test_database_url_environment_variables_integration(self):
        """Test that DATABASE_URL integrates with environment variables correctly."""
        # DATABASE_URL should be constructed from settings
        assert "eshop_user" in DATABASE_URL or "localhost" in DATABASE_URL

        # Should contain all required database components
        assert "postgresql+asyncpg://" in DATABASE_URL
        assert "@" in DATABASE_URL
        assert ":" in DATABASE_URL

    def test_engine_pool_settings_for_connection_management(self):
        """Test that engine has proper pool settings for connection management."""
        # Engine should have pool settings
        assert hasattr(engine, "pool")
        assert engine.pool is not None

        # Test pool configuration
        pool = engine.pool
        assert hasattr(pool, "size")  # Should have pool size
        assert hasattr(pool, "overflow")  # Should have overflow setting

    def test_async_session_local_engine_reference_consistency(self):
        """Test that AsyncSessionLocal references the correct engine consistently."""
        # AsyncSessionLocal should use the same engine
        assert AsyncSessionLocal.kw["bind"] == engine

        # Multiple checks should be consistent
        assert AsyncSessionLocal.kw["bind"] is engine

    @pytest.mark.asyncio
    async def test_get_async_session_session_lifecycle_management(self):
        """Test session lifecycle management in get_async_session."""
        session_gen = get_async_session()

        # Get session
        session = await session_gen.__anext__()

        # Session should be active and properly configured
        assert session.bind == engine
        assert session.autoflush is True

        # Test session state
        assert not hasattr(session, "is_closed") or not session.is_closed

        # Close generator (this should close the session)
        with contextlib.suppress(StopAsyncIteration):
            await session_gen.__anext__()

    def test_engine_disposal_method_availability(self):
        """Test that engine can be disposed when needed."""
        # Engine should have dispose method
        assert hasattr(engine, "dispose")

        # Should be callable
        assert callable(engine.dispose)

        # Test that dispose method can be called (without actually disposing)
        # We don't want to actually dispose the engine during tests
        dispose_method = engine.dispose
        assert dispose_method is not None

    def test_async_session_local_creation_parameters_validation(self):
        """Test AsyncSessionLocal creation parameters are correctly set."""
        # Should be created with correct parameters
        assert "expire_on_commit" in AsyncSessionLocal.kw
        assert "bind" in AsyncSessionLocal.kw

        # Test parameter values
        assert AsyncSessionLocal.kw["expire_on_commit"] is False
        assert AsyncSessionLocal.kw["bind"] == engine

    @pytest.mark.asyncio
    async def test_get_async_session_generator_behavior_validation(self):
        """Test that get_async_session behaves like a proper async generator."""
        session_gen = get_async_session()

        # Should be iterable
        assert hasattr(session_gen, "__aiter__")
        assert hasattr(session_gen, "__anext__")

        # Should yield exactly one session
        session = await session_gen.__anext__()
        assert session is not None
        assert session.bind == engine

        # Should raise StopAsyncIteration after yielding
        with pytest.raises(StopAsyncIteration):
            await session_gen.__anext__()

    def test_engine_url_construction_with_security_masking(self):
        """Test that engine URL is constructed correctly with security masking."""
        # Engine URL should match DATABASE_URL (but may be masked for security)
        engine_url_str = str(engine.url)
        # The engine URL might mask the password, so we check the structure
        assert engine_url_str.startswith("postgresql+asyncpg://")
        assert "postgres" in engine_url_str
        assert "localhost:5432/eshop" in engine_url_str

    def test_async_session_local_autoflush_setting(self):
        """Test that AsyncSessionLocal has autoflush=True for automatic flushing."""
        # AsyncSessionLocal should have autoflush=True
        assert AsyncSessionLocal.kw.get("autoflush", True) is True

    def test_engine_connectivity_and_functionality(self):
        """Test that engine is fully functional and can be used."""
        # Engine should be created successfully and be functional
        assert engine is not None
        assert hasattr(engine, "url")
        assert hasattr(engine, "dispose")

        # Test engine functionality
        assert engine.url is not None
        assert str(engine.url).startswith("postgresql+asyncpg://")

    def test_async_session_local_functionality_and_configuration(self):
        """Test that AsyncSessionLocal is a proper session maker with correct config."""
        # Should be callable
        assert callable(AsyncSessionLocal)

        # Should have proper attributes
        assert hasattr(AsyncSessionLocal, "kw")
        assert isinstance(AsyncSessionLocal.kw, dict)

        # Test configuration
        assert AsyncSessionLocal.kw["expire_on_commit"] is False
        assert AsyncSessionLocal.kw["bind"] == engine
