"""Pytest tests for database migration system."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.core.database.migrations import (
    _create_alembic_config,
    _create_migrations_directory,
    create_initial_migration,
    run_migrations,
)


class TestDatabaseMigrations:
    """Test database migration functionality."""

    def test_create_alembic_config(self, tmp_path, monkeypatch):
        """Test Alembic configuration creation."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        # Test configuration creation
        _create_alembic_config()

        # Verify alembic.ini was created
        alembic_ini = tmp_path / "alembic.ini"
        assert alembic_ini.exists()

        # Verify content contains expected sections
        content = alembic_ini.read_text()
        assert "[alembic]" in content
        assert "script_location = migrations" in content
        assert "sqlalchemy.url" in content

    def test_create_migrations_directory(self, tmp_path, monkeypatch):
        """Test migrations directory structure creation."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        # Test directory creation
        _create_migrations_directory()

        # Verify directory structure
        migrations_dir = tmp_path / "migrations"
        assert migrations_dir.exists()

        versions_dir = migrations_dir / "versions"
        assert versions_dir.exists()

        env_py = migrations_dir / "env.py"
        assert env_py.exists()

        script_mako = migrations_dir / "script.py.mako"
        assert script_mako.exists()

        # Verify env.py content
        env_content = env_py.read_text()
        assert "from app.core.database.base import Base" in env_content
        assert "target_metadata = Base.metadata" in env_content

    @patch("asyncio.create_subprocess_exec")
    async def test_run_migrations_success(self, mock_create_subprocess, tmp_path, monkeypatch):
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
            "poetry", "run", "alembic", "upgrade", "head",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=tmp_path,
        )

    @patch("asyncio.create_subprocess_exec")
    async def test_run_migrations_failure(self, mock_create_subprocess, tmp_path, monkeypatch):
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

    @patch("subprocess.run")
    def test_create_initial_migration_success(self, mock_run, tmp_path, monkeypatch):
        """Test successful initial migration creation."""
        # Mock successful subprocess run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Migration created successfully"
        mock_run.return_value = mock_result

        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        # Test migration creation
        create_initial_migration()

        # Verify subprocess was called correctly
        mock_run.assert_called_once_with(
            [
                "poetry",
                "run",
                "alembic",
                "revision",
                "--autogenerate",
                "-m",
                "Initial migration",
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

    @patch("subprocess.run")
    def test_create_initial_migration_failure(self, mock_run, tmp_path, monkeypatch):
        """Test initial migration creation failure."""
        # Mock failed subprocess run
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Migration creation failed"
        mock_run.return_value = mock_result

        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        # Test migration creation failure
        with pytest.raises(RuntimeError, match="Migration creation failed"):
            create_initial_migration()

    async def test_run_migrations_creates_config_if_missing(self, tmp_path, monkeypatch):
        """Test that run_migrations creates config if missing."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        # Mock subprocess to avoid actual execution
        with patch("asyncio.create_subprocess_exec") as mock_create_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            
            async def mock_communicate():
                return (b"Migration completed", b"")
            
            mock_process.communicate = mock_communicate
            mock_create_subprocess.return_value = mock_process

            # Run migrations (should create config)
            await run_migrations()

            # Verify config was created
            assert (tmp_path / "alembic.ini").exists()
            assert (tmp_path / "migrations").exists()
            assert (tmp_path / "migrations" / "env.py").exists()
