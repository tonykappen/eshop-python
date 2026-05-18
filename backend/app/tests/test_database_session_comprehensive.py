"""Comprehensive tests for database session management."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.database.session import (AsyncSessionLocal, close_db_engine,
                                       create_db_engine, engine,
                                       get_db_session, get_pool_status)
from app.core.exceptions.common_exceptions import DatabaseError
from sqlalchemy.exc import SQLAlchemyError


class TestDatabaseSession:
    """Test cases for database session management."""

    def test_engine_creation(self):
        """Test that the database engine is created correctly."""
        assert engine is not None
        assert hasattr(engine, "url")
        assert hasattr(engine, "pool")

    def test_async_session_local_creation(self):
        """Test that AsyncSessionLocal is created correctly."""
        assert AsyncSessionLocal is not None
        assert hasattr(AsyncSessionLocal, "begin")

    @pytest.mark.asyncio
    async def test_get_db_session_success(self):
        """Test successful database session retrieval."""
        with patch("app.core.database.session.AsyncSessionLocal") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value = mock_session

            async for _ in get_db_session():
                break  # Only test the first iteration

            mock_factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_handles_exceptions(self):
        """Test that get_db_session handles exceptions properly."""
        with patch("app.core.database.session.AsyncSessionLocal") as mock_factory:
            mock_factory.side_effect = SQLAlchemyError("Database connection failed")

            with pytest.raises(SQLAlchemyError):
                async for _ in get_db_session():
                    pass

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
            mock_engine.pool = None  # Simulate missing pool

            result = await get_pool_status()
            assert "error" in result

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
    async def test_create_db_engine_handles_exceptions(self):
        """Test that create_db_engine handles exceptions properly."""
        with patch("app.core.database.session.engine") as mock_engine:
            mock_engine.begin.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(DatabaseError):
                await create_db_engine()

    @pytest.mark.asyncio
    async def test_close_db_engine_success(self):
        """Test successful database engine closure."""
        with patch("app.core.database.session.engine") as mock_engine:
            await close_db_engine()
            mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_engine_handles_exceptions(self):
        """Test that close_db_engine handles exceptions properly."""
        with patch("app.core.database.session.engine") as mock_engine:
            mock_engine.dispose.side_effect = Exception("Dispose failed")

            # Should not raise exception
            await close_db_engine()

    def test_session_context_manager(self):
        """Test that the session context manager works correctly."""
        with patch("app.core.database.session.AsyncSessionLocal") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value = mock_session

            # Test context manager behavior
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

    @pytest.mark.asyncio
    async def test_get_db_session_with_rollback(self):
        """Test that get_db_session rolls back on exception."""
        with patch("app.core.database.session.AsyncSessionLocal") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value = mock_session

            # Simulate an exception during session usage
            async def mock_session_generator():
                yield mock_session
                raise SQLAlchemyError("Database error")

            with patch(
                "app.core.database.session.get_db_session", mock_session_generator
            ):
                with pytest.raises(SQLAlchemyError):
                    async for _ in get_db_session():
                        pass

                # Verify rollback was called
                mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_with_close(self):
        """Test that get_db_session closes session properly."""
        with patch("app.core.database.session.AsyncSessionLocal") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value = mock_session

            async for _ in get_db_session():
                break  # Only test the first iteration

            # Verify close was called
            mock_session.close.assert_called_once()

    def test_engine_configuration(self):
        """Test that the engine is configured correctly."""
        assert engine.pool_size == 10
        assert engine.max_overflow == 20
        assert engine.pool_pre_ping is True
        assert engine.pool_recycle == 300
        assert engine.pool_timeout == 30

    def test_async_session_local_configuration(self):
        """Test that AsyncSessionLocal is configured correctly."""
        assert AsyncSessionLocal.kw.get("expire_on_commit") is False
        assert AsyncSessionLocal.kw.get("autoflush") is False
        assert AsyncSessionLocal.kw.get("autocommit") is False
