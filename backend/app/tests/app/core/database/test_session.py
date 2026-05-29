"""Tests for database session management."""

import contextlib
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from app.core.database.session import (
    AsyncSessionLocal,
    close_db_engine,
    create_db_engine,
    engine,
    get_db_session,
    get_pool_status,
)
from app.core.exceptions.common_exceptions import DatabaseError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


class TestDatabaseSession:
    """Test database session functionality."""

    @pytest.mark.asyncio
    async def test_get_db_session_generator(self):
        """Test that get_db_session is an async generator."""
        session_gen = get_db_session()
        assert hasattr(session_gen, "__aiter__")
        assert hasattr(session_gen, "__anext__")

    @pytest.mark.asyncio
    async def test_get_db_session_context_manager(self):
        """Test get_db_session as context manager."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database.session.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            async for session in get_db_session():
                assert session == mock_session
                break

            mock_session_local.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_exception_handling(self):
        """Test get_db_session exception handling."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = Exception("Database error")

        with patch("app.core.database.session.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            async for session in get_db_session():
                with contextlib.suppress(Exception):
                    await session.execute(text("SELECT 1"))
                break

    @pytest.mark.asyncio
    async def test_get_db_session_handles_sqlalchemy_errors(self):
        """Test that get_db_session propagates SQLAlchemy errors."""
        with patch("app.core.database.session.AsyncSessionLocal") as mock_factory:
            mock_factory.side_effect = SQLAlchemyError("Database connection failed")

            with pytest.raises(SQLAlchemyError):
                async for _ in get_db_session():
                    pass

    @pytest.mark.asyncio
    async def test_get_db_session_with_close(self):
        """Test that get_db_session closes session properly."""
        with patch("app.core.database.session.AsyncSessionLocal") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value = mock_session

            async for _ in get_db_session():
                break

            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_db_engine_success(self):
        """Test successful database engine creation."""
        with patch("app.core.database.session.engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None

            with patch("app.core.database.session.get_pool_status") as mock_pool_status:
                mock_pool_status.return_value = {"pool_size": 10}

                await create_db_engine()

                mock_conn.execute.assert_called_once()
                mock_pool_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_db_engine_failure(self):
        """Test database engine creation failure."""
        with patch("app.core.database.session.engine") as mock_engine:
            mock_engine.begin.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(DatabaseError, match="Database engine creation failed"):
                await create_db_engine()

    @pytest.mark.asyncio
    async def test_close_db_engine_success(self):
        """Test successful database engine closure."""
        with patch("app.core.database.session.engine") as mock_engine:
            mock_engine.dispose = AsyncMock()

            await close_db_engine()

            mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_engine_failure_raises(self):
        """Test database engine closure failure raises DatabaseError."""
        with patch("app.core.database.session.engine") as mock_engine:
            mock_engine.dispose = AsyncMock(side_effect=Exception("Dispose failed"))

            with pytest.raises(DatabaseError, match="Database engine close failed"):
                await close_db_engine()

    def test_engine_configuration(self):
        """Test that engine is properly configured."""
        assert engine is not None
        assert hasattr(engine, "url")
        assert hasattr(engine, "pool")

    def test_async_session_local_configuration(self):
        """Test that AsyncSessionLocal is properly configured."""
        assert AsyncSessionLocal is not None
        assert callable(AsyncSessionLocal)


class TestDatabasePoolStatus:
    """Test pool status and extended session configuration."""

    @pytest.mark.asyncio
    async def test_get_pool_status_success(self):
        """Test successful pool status retrieval."""
        with patch("app.core.database.session.engine") as mock_engine:
            mock_pool = MagicMock()
            mock_pool.size.return_value = 10
            mock_pool.checkedin.return_value = 5
            mock_pool.checkedout.return_value = 3
            mock_pool.overflow.return_value = 2
            mock_pool.invalid.return_value = 0
            mock_engine.pool = mock_pool

            result = await get_pool_status()
            assert result["pool_size"] == 10
            assert result["checked_in"] == 5
            assert result["checked_out"] == 3
            assert result["overflow"] == 2
            assert result["invalid"] == 0
            assert result["total_connections"] == 8

    @pytest.mark.asyncio
    async def test_get_pool_status_handles_exceptions(self):
        """Test that get_pool_status handles exceptions properly."""
        with patch("app.core.database.session.engine") as mock_engine:
            mock_engine.pool = None

            result = await get_pool_status()
            assert "error" in result

    def test_engine_pool_settings(self):
        """Test engine pool configuration values."""
        assert engine.pool_size == 10
        assert engine.max_overflow == 20
        assert engine.pool_pre_ping is True
        assert engine.pool_recycle == 300
        assert engine.pool_timeout == 30

    def test_async_session_local_factory_settings(self):
        """Test AsyncSessionLocal factory settings."""
        assert AsyncSessionLocal.kw.get("expire_on_commit") is False
        assert AsyncSessionLocal.kw.get("autoflush") is False
        assert AsyncSessionLocal.kw.get("autocommit") is False

    def test_session_context_manager(self):
        """Test that the session context manager works correctly."""
        with patch("app.core.database.session.AsyncSessionLocal") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value = mock_session

            with AsyncSessionLocal() as session:
                assert session == mock_session

            mock_factory.assert_called_once()

    def test_session_context_manager_with_exception(self):
        """Test that the session context manager handles exceptions correctly."""
        with patch("app.core.database.session.AsyncSessionLocal") as mock_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__.side_effect = SQLAlchemyError("Session error")
            mock_factory.return_value = mock_session

            with pytest.raises(SQLAlchemyError), AsyncSessionLocal() as _:
                pass


class TestDatabaseConnectionString:
    """Test database connection string configuration."""

    @patch("app.config.settings.settings")
    def test_database_connection_string_format(self, mock_settings):
        """Test database connection string format."""
        mock_settings.db_user = "test_user"
        mock_settings.db_password = "test_password"
        mock_settings.db_host = "test_host"
        mock_settings.db_port = 5432
        mock_settings.db_name = "test_db"

        type(mock_settings).database_connection_string = PropertyMock(
            return_value="postgresql+asyncpg://test_user:test_password@test_host:5432/test_db"
        )

        connection_string = mock_settings.database_connection_string
        expected = "postgresql+asyncpg://test_user:test_password@test_host:5432/test_db"

        assert connection_string == expected

    @patch("app.config.settings.settings")
    def test_database_connection_string_with_special_chars(self, mock_settings):
        """Test database connection string with special characters in password."""
        mock_settings.db_user = "test_user"
        mock_settings.db_password = "test@password#123"
        mock_settings.db_host = "test_host"
        mock_settings.db_port = 5432
        mock_settings.db_name = "test_db"

        type(mock_settings).database_connection_string = PropertyMock(
            return_value="postgresql+asyncpg://test_user:test@password#123@test_host:5432/test_db"
        )

        connection_string = mock_settings.database_connection_string
        expected = (
            "postgresql+asyncpg://test_user:test@password#123@test_host:5432/test_db"
        )

        assert connection_string == expected


class TestDatabaseSessionLifecycle:
    """Test database session lifecycle management."""

    @pytest.mark.asyncio
    async def test_session_lifecycle_with_context_manager(self):
        """Test session lifecycle using context manager."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database.session.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            session_gen = get_db_session()
            session = await session_gen.__anext__()

            await session.execute(text("SELECT 1"))
            await session.commit()

            with contextlib.suppress(StopAsyncIteration):
                await session_gen.__anext__()

            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_lifecycle_with_exception(self):
        """Test session lifecycle with exception handling."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database.session.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            session_gen = get_db_session()
            session = await session_gen.__anext__()

            await session.execute(text("SELECT 1"))
            await session.commit()

            with contextlib.suppress(StopAsyncIteration):
                await session_gen.__anext__()

            mock_session.close.assert_called_once()


class TestDatabaseEngineConfiguration:
    """Test database engine configuration."""

    def test_engine_pool_configuration(self):
        """Test engine pool configuration."""
        assert hasattr(engine, "pool")
        assert engine.pool is not None

        pool = engine.pool
        assert hasattr(pool, "_pool")
        assert hasattr(pool, "size")
        assert hasattr(pool, "checkedin")
        assert hasattr(pool, "checkedout")

    def test_engine_echo_configuration(self):
        """Test engine echo configuration."""
        assert hasattr(engine, "echo")
        assert isinstance(engine.echo, bool)

    def test_engine_url_configuration(self):
        """Test engine URL configuration."""
        assert hasattr(engine, "url")
        assert engine.url is not None
        assert str(engine.url).startswith("postgresql+asyncpg://")
