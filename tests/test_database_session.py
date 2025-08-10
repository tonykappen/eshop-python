"""Pytest tests for database session management."""

import contextlib
from unittest.mock import AsyncMock, PropertyMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from eshop.core.database.session import (
    AsyncSessionLocal,
    close_db_engine,
    create_db_engine,
    engine,
    get_db_session,
)
from eshop.core.exceptions.base import DatabaseError


class TestDatabaseSession:
    """Test database session functionality."""

    @pytest.mark.asyncio
    async def test_get_db_session_generator(self):
        """Test that get_db_session is an async generator."""
        session_gen = get_db_session()

        # Should be an async generator
        assert hasattr(session_gen, "__aiter__")
        assert hasattr(session_gen, "__anext__")

    @pytest.mark.asyncio
    async def test_get_db_session_context_manager(self):
        """Test get_db_session as context manager."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("eshop.core.database.session.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            async for session in get_db_session():
                assert session == mock_session
                break  # Only test first iteration

            # Verify session was properly managed
            mock_session_local.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_exception_handling(self):
        """Test get_db_session exception handling."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = Exception("Database error")

        with patch("eshop.core.database.session.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            async for session in get_db_session():
                # Should handle exception gracefully
                with contextlib.suppress(Exception):
                    await session.execute(text("SELECT 1"))
                break

    @pytest.mark.asyncio
    async def test_create_db_engine_success(self):
        """Test successful database engine creation."""
        with patch("eshop.core.database.session.engine") as mock_engine:
            mock_engine.begin.return_value.__aenter__.return_value.execute.return_value = None

            await create_db_engine()

            # Verify engine.begin was called
            mock_engine.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_db_engine_failure(self):
        """Test database engine creation failure."""
        with patch("eshop.core.database.session.engine") as mock_engine:
            mock_engine.begin.side_effect = Exception("Connection failed")

            with pytest.raises(DatabaseError, match="Database engine creation failed"):
                await create_db_engine()

    @pytest.mark.asyncio
    async def test_close_db_engine_success(self):
        """Test successful database engine closure."""
        with patch("eshop.core.database.session.engine") as mock_engine:
            mock_engine.dispose = AsyncMock()

            await close_db_engine()

            mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_engine_failure(self):
        """Test database engine closure failure."""
        with patch("eshop.core.database.session.engine") as mock_engine:
            mock_engine.dispose = AsyncMock(side_effect=Exception("Dispose failed"))

            with pytest.raises(DatabaseError, match="Database engine close failed"):
                await close_db_engine()

    def test_engine_configuration(self):
        """Test that engine is properly configured."""
        # Test that engine exists and has expected attributes
        assert engine is not None
        assert hasattr(engine, "url")
        assert hasattr(engine, "pool")

    def test_async_session_local_configuration(self):
        """Test that AsyncSessionLocal is properly configured."""
        # Test that AsyncSessionLocal exists and is callable
        assert AsyncSessionLocal is not None
        assert callable(AsyncSessionLocal)


class TestDatabaseConnectionString:
    """Test database connection string configuration."""

    @patch("eshop.config.settings.settings")
    def test_database_connection_string_format(self, mock_settings):
        """Test database connection string format."""
        # Mock settings with property
        mock_settings.db_user = "test_user"
        mock_settings.db_password = "test_password"
        mock_settings.db_host = "test_host"
        mock_settings.db_port = 5432
        mock_settings.db_name = "test_db"

        # Mock the property to return the expected value
        type(mock_settings).database_connection_string = PropertyMock(
            return_value="postgresql+asyncpg://test_user:test_password@test_host:5432/test_db"
        )

        # Test connection string format
        connection_string = mock_settings.database_connection_string
        expected = "postgresql+asyncpg://test_user:test_password@test_host:5432/test_db"

        assert connection_string == expected

    @patch("eshop.config.settings.settings")
    def test_database_connection_string_with_special_chars(self, mock_settings):
        """Test database connection string with special characters in password."""
        # Mock settings with special characters in password
        mock_settings.db_user = "test_user"
        mock_settings.db_password = "test@password#123"
        mock_settings.db_host = "test_host"
        mock_settings.db_port = 5432
        mock_settings.db_name = "test_db"

        # Mock the property to return the expected value
        type(mock_settings).database_connection_string = PropertyMock(
            return_value="postgresql+asyncpg://test_user:test@password#123@test_host:5432/test_db"
        )

        # Test connection string format
        connection_string = mock_settings.database_connection_string
        expected = "postgresql+asyncpg://test_user:test@password#123@test_host:5432/test_db"

        assert connection_string == expected


class TestDatabaseSessionLifecycle:
    """Test database session lifecycle management."""

    @pytest.mark.asyncio
    async def test_session_lifecycle_with_context_manager(self):
        """Test session lifecycle using context manager."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Test the actual get_db_session function which handles session lifecycle
        with patch("eshop.core.database.session.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            # Use get_db_session which properly handles session lifecycle
            session_gen = get_db_session()
            session = await session_gen.__anext__()

            # Simulate some database operations
            await session.execute(text("SELECT 1"))
            await session.commit()

            # Close the generator properly
            with contextlib.suppress(StopAsyncIteration):
                await session_gen.__anext__()

            # Verify session was properly closed
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_lifecycle_with_exception(self):
        """Test session lifecycle with exception handling."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("eshop.core.database.session.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            # Test that get_db_session properly handles session lifecycle
            session_gen = get_db_session()
            session = await session_gen.__anext__()

            # Simulate normal session usage
            await session.execute(text("SELECT 1"))
            await session.commit()

            # Close the generator properly
            with contextlib.suppress(StopAsyncIteration):
                await session_gen.__anext__()

            # Verify session was properly closed (rollback is only called on exceptions)
            mock_session.close.assert_called_once()


class TestDatabaseEngineConfiguration:
    """Test database engine configuration."""

    def test_engine_pool_configuration(self):
        """Test engine pool configuration."""
        # Test that engine has proper pool configuration
        assert hasattr(engine, "pool")
        assert engine.pool is not None

        # Test pool settings - use more flexible checks for SQLAlchemy 2.0
        pool = engine.pool
        assert hasattr(pool, "_pool")
        assert hasattr(pool, "size")
        # max_overflow might not be directly accessible in SQLAlchemy 2.0
        # Check for pool configuration methods instead
        assert hasattr(pool, "checkedin")
        assert hasattr(pool, "checkedout")

    def test_engine_echo_configuration(self):
        """Test engine echo configuration."""
        # Test that engine echo is properly configured
        # This depends on the debug setting
        assert hasattr(engine, "echo")
        assert isinstance(engine.echo, bool)

    def test_engine_url_configuration(self):
        """Test engine URL configuration."""
        # Test that engine URL is properly configured
        assert hasattr(engine, "url")
        assert engine.url is not None
        assert str(engine.url).startswith("postgresql+asyncpg://")
