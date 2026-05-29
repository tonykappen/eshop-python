"""Pytest tests for database migration system."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from app.core.database.migrations import (create_module_migration,
                                          ensure_schemas_exist, run_migrations,
                                          wait_for_database)


class TestDatabaseMigrations:
    """Test database migration functionality."""

    async def test_wait_for_database(self):
        """Test database connection waiting."""
        # This test would require a real database connection
        # For now, we'll just test that the function exists and can be called
        with pytest.raises(ConnectionError):  # Should fail without real DB
            await wait_for_database(max_retries=1, delay=0.1)

    @patch("app.core.database.migrations.AsyncSessionLocal")
    async def test_ensure_schemas_exist(self, mock_session_local):
        """Test schema existence check."""
        from unittest.mock import AsyncMock

        # Mock session that raises an exception (simulating DB connection failure)
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute.side_effect = Exception("Database connection failed")
        mock_session_local.return_value = mock_session

        # Should raise exception when DB connection fails
        with pytest.raises(Exception, match="Database connection failed"):
            await ensure_schemas_exist()

    @patch("asyncio.create_subprocess_exec")
    async def test_run_migrations_success(
        self, mock_create_subprocess, tmp_path, monkeypatch
    ):
        """Test successful migration execution."""
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.returncode = 0

        async def mock_communicate():
            return (b"Migration completed successfully", b"")

        mock_process.communicate = mock_communicate
        mock_create_subprocess.return_value = mock_process

        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        # Create required files
        (tmp_path / "alembic.ini").touch()
        (tmp_path / "migrations").mkdir()

        # Test migration execution
        await run_migrations()

        # Verify subprocess was called correctly
        mock_create_subprocess.assert_called_once_with(
            "poetry",
            "run",
            "alembic",
            "upgrade",
            "head",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=tmp_path,
        )

    @patch("asyncio.create_subprocess_exec")
    async def test_run_migrations_failure(
        self, mock_create_subprocess, tmp_path, monkeypatch
    ):
        """Test migration execution failure."""
        # Mock failed subprocess
        mock_process = MagicMock()
        mock_process.returncode = 1

        async def mock_communicate():
            return (b"", b"Migration failed")

        mock_process.communicate = mock_communicate
        mock_create_subprocess.return_value = mock_process

        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        # Create required files
        (tmp_path / "alembic.ini").touch()
        (tmp_path / "migrations").mkdir()

        # Test migration execution failure
        with pytest.raises(RuntimeError, match="Migration failed"):
            await run_migrations()

    @patch("asyncio.create_subprocess_exec")
    async def test_create_module_migration_success(self, mock_create_subprocess):
        """Test successful module migration creation."""
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.returncode = 0

        async def mock_communicate():
            return (b"Migration created successfully", b"")

        mock_process.communicate = mock_communicate
        mock_create_subprocess.return_value = mock_process

        # Test migration creation
        await create_module_migration("catalog", "Test migration")

        # Verify subprocess was called correctly
        mock_create_subprocess.assert_called_once()

    @patch("asyncio.create_subprocess_exec")
    async def test_create_module_migration_failure(self, mock_create_subprocess):
        """Test module migration creation failure."""
        # Mock failed subprocess
        mock_process = MagicMock()
        mock_process.returncode = 1

        async def mock_communicate():
            return (b"", b"Migration creation failed")

        mock_process.communicate = mock_communicate
        mock_create_subprocess.return_value = mock_process

        # Test migration creation failure
        with pytest.raises(RuntimeError, match="Migration creation failed"):
            await create_module_migration("catalog", "Test migration")

    def test_create_module_migration_invalid_module(self):
        """Test migration creation with invalid module name."""
        with pytest.raises(ValueError, match="Module invalid_module not found"):
            # This will fail because the module doesn't exist in MODULE_CONFIGS
            asyncio.run(create_module_migration("invalid_module", "Test migration"))
