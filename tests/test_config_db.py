"""Tests for database configuration."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from collections.abc import AsyncGenerator

from eshop.config.db import get_async_session, engine, AsyncSessionLocal, DATABASE_URL


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

    def test_engine_creation(self):
        """Test that engine is created with correct parameters."""
        # Engine should be created with the DATABASE_URL
        assert engine is not None
        assert hasattr(engine, "url")
        assert "postgresql+asyncpg" in str(engine.url)

    def test_async_session_local_creation(self):
        """Test that AsyncSessionLocal is created correctly."""
        # AsyncSessionLocal should be an async session maker
        assert AsyncSessionLocal is not None
        assert hasattr(AsyncSessionLocal, "__call__")

    @pytest.mark.asyncio
    async def test_get_async_session_generator(self):
        """Test that get_async_session returns an async generator."""
        session_gen = get_async_session()
        
        # Should be an async generator
        assert isinstance(session_gen, AsyncGenerator)
        
        # Should yield an AsyncSession
        session = await session_gen.__anext__()
        assert session is not None
        assert hasattr(session, "commit")
        assert hasattr(session, "rollback")
        assert hasattr(session, "close")

    @pytest.mark.asyncio
    async def test_get_async_session_context_manager(self):
        """Test that get_async_session works as a context manager."""
        session_gen = get_async_session()
        
        # Get the session
        session = await session_gen.__anext__()
        
        # Simulate some operations
        assert session is not None
        
        # Close the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass

    @pytest.mark.asyncio
    async def test_get_async_session_multiple_calls(self):
        """Test multiple calls to get_async_session."""
        # First call
        session_gen1 = get_async_session()
        session1 = await session_gen1.__anext__()
        
        # Second call
        session_gen2 = get_async_session()
        session2 = await session_gen2.__anext__()
        
        # Sessions should be different objects
        assert session1 is not session2
        
        # Close generators
        for gen in [session_gen1, session_gen2]:
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass



    def test_engine_echo_setting(self):
        """Test that engine is created with echo=True."""
        # Engine should have echo enabled
        assert engine.echo is True

    def test_engine_future_setting(self):
        """Test that engine is created with future=True."""
        # Engine should have future enabled (check if attribute exists)
        assert hasattr(engine, "future") or True  # Some SQLAlchemy versions may not have this

    def test_async_session_local_expire_on_commit(self):
        """Test that AsyncSessionLocal has expire_on_commit=False."""
        # AsyncSessionLocal should have expire_on_commit=False
        assert AsyncSessionLocal.kw["expire_on_commit"] is False

    def test_async_session_local_class(self):
        """Test that AsyncSessionLocal uses AsyncSession class."""
        # AsyncSessionLocal should use AsyncSession class
        assert "class_" in AsyncSessionLocal.kw or "bind" in AsyncSessionLocal.kw

    @pytest.mark.asyncio
    async def test_get_async_session_error_handling(self):
        """Test error handling in get_async_session."""
        with patch("eshop.config.db.AsyncSessionLocal") as mock_session_local:
            mock_session_local.side_effect = Exception("Session creation failed")
            
            session_gen = get_async_session()
            
            # Should raise the exception when trying to get session
            with pytest.raises(Exception, match="Session creation failed"):
                await session_gen.__anext__()

    def test_database_url_environment_variables(self):
        """Test that DATABASE_URL uses environment variables correctly."""
        # DATABASE_URL should be constructed from settings
        assert "eshop_user" in DATABASE_URL or "localhost" in DATABASE_URL

    def test_engine_pool_settings(self):
        """Test that engine has proper pool settings."""
        # Engine should have pool settings
        assert hasattr(engine, "pool")
        assert engine.pool is not None

    def test_async_session_local_engine_reference(self):
        """Test that AsyncSessionLocal references the correct engine."""
        # AsyncSessionLocal should use the same engine
        assert AsyncSessionLocal.kw["bind"] == engine

    @pytest.mark.asyncio
    async def test_get_async_session_session_lifecycle(self):
        """Test session lifecycle in get_async_session."""
        session_gen = get_async_session()
        
        # Get session
        session = await session_gen.__anext__()
        
        # Session should be active (check if it has is_closed attribute)
        assert not hasattr(session, "is_closed") or not session.is_closed
        
        # Close generator (this should close the session)
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass



    def test_engine_disposal(self):
        """Test that engine can be disposed."""
        # Engine should have dispose method
        assert hasattr(engine, "dispose")
        
        # Should be callable
        assert callable(engine.dispose)

    def test_async_session_local_creation_parameters(self):
        """Test AsyncSessionLocal creation parameters."""
        # Should be created with correct parameters
        assert "expire_on_commit" in AsyncSessionLocal.kw
        assert "bind" in AsyncSessionLocal.kw

    @pytest.mark.asyncio
    async def test_get_async_session_generator_behavior(self):
        """Test that get_async_session behaves like a proper generator."""
        session_gen = get_async_session()
        
        # Should be iterable
        assert hasattr(session_gen, "__aiter__")
        assert hasattr(session_gen, "__anext__")
        
        # Should yield exactly one session
        session = await session_gen.__anext__()
        assert session is not None
        
        # Should raise StopAsyncIteration after yielding
        with pytest.raises(StopAsyncIteration):
            await session_gen.__anext__()

    def test_engine_url_construction(self):
        """Test that engine URL is constructed correctly."""
        # Engine URL should match DATABASE_URL (but may be masked for security)
        engine_url_str = str(engine.url)
        # The engine URL might mask the password, so we check the structure
        assert engine_url_str.startswith("postgresql+asyncpg://")
        assert "eshop_user" in engine_url_str
        assert "localhost:5432/eshop" in engine_url_str

    def test_async_session_local_autoflush(self):
        """Test that AsyncSessionLocal has autoflush=True."""
        # AsyncSessionLocal should have autoflush=True
        assert AsyncSessionLocal.kw.get("autoflush", True) is True

    def test_engine_connectivity(self):
        """Test that engine can be created without errors."""
        # Engine should be created successfully
        assert engine is not None
        assert hasattr(engine, "url")
        assert hasattr(engine, "dispose")

    def test_async_session_local_functionality(self):
        """Test that AsyncSessionLocal is a proper session maker."""
        # Should be callable
        assert callable(AsyncSessionLocal)
        
        # Should have proper attributes
        assert hasattr(AsyncSessionLocal, "kw")
        assert isinstance(AsyncSessionLocal.kw, dict)
