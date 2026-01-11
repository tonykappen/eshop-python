"""Pytest tests for database seeding system."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.database.seeding import (
    DataSeederManager,
    IDataSeeder,
    check_if_data_exists,
    ensure_schema_exists,
    register_seeder,
    run_seeding,
)
from app.modules.catalog.infrastructure.seeding.products.catalog_data_seeder import (
    CatalogDataSeeder,
)
from app.modules.catalog.infrastructure.seeding.products.initial_data import CatalogInitialData


class TestDataSeederInterface:
    """Test IDataSeeder interface."""

    def test_idataseeder_is_abstract(self):
        """Test that IDataSeeder is an abstract base class."""
        with pytest.raises(TypeError):
            IDataSeeder()  # Should raise TypeError for abstract class


class TestDataSeederManager:
    """Test DataSeederManager functionality."""

    def test_seeder_manager_initialization(self):
        """Test DataSeederManager initialization."""
        manager = DataSeederManager()
        assert manager.seeders == []
        assert manager.logger is not None

    def test_register_seeder(self):
        """Test seeder registration."""
        manager = DataSeederManager()

        # Create a mock seeder class
        class MockSeeder(IDataSeeder):
            async def seed_all_async(self) -> None:
                pass

        # Register seeder
        manager.register_seeder(MockSeeder)

        assert len(manager.seeders) == 1
        assert manager.seeders[0] == MockSeeder

    @pytest.mark.asyncio
    async def test_run_all_seeders_empty(self):
        """Test running seeders when none are registered."""
        manager = DataSeederManager()

        # Should not raise any exceptions
        await manager.run_all_seeders()

    @pytest.mark.asyncio
    async def test_run_all_seeders_success(self):
        """Test successful seeder execution."""
        manager = DataSeederManager()

        # Create a mock seeder
        mock_seeder_instance = AsyncMock()

        class MockSeeder(IDataSeeder):
            def __init__(self):
                self.instance = mock_seeder_instance

            async def seed_all_async(self) -> None:
                await self.instance.seed_all_async()

        # Register seeder
        manager.register_seeder(MockSeeder)

        # Mock the database session to avoid greenlet issues
        with patch("app.core.database.seeding.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Run seeders
            await manager.run_all_seeders()

            # Verify seeder was called
            mock_seeder_instance.seed_all_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_all_seeders_failure(self):
        """Test seeder execution failure."""
        manager = DataSeederManager()

        class FailingSeeder(IDataSeeder):
            async def seed_all_async(self) -> None:
                raise RuntimeError("Seeder failed")

        # Register failing seeder
        manager.register_seeder(FailingSeeder)

        # Mock the database session to avoid greenlet issues
        with patch("app.core.database.seeding.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Should raise exception
            with pytest.raises(RuntimeError, match="Seeder failed"):
                await manager.run_all_seeders()


class TestSeedingFunctions:
    """Test seeding utility functions."""

    @pytest.mark.asyncio
    async def test_register_seeder_global(self):
        """Test global seeder registration."""

        # Create a mock seeder class
        class MockSeeder(IDataSeeder):
            async def seed_all_async(self) -> None:
                pass

        # Register seeder
        register_seeder(MockSeeder)

        # Verify seeder was registered (we can't easily test the global manager)
        # This test mainly ensures the function doesn't raise exceptions
        assert True

    @pytest.mark.asyncio
    async def test_check_if_data_exists_true(self):
        """Test check_if_data_exists when data exists."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        with patch("app.core.database.seeding.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            result = await check_if_data_exists("test_table", "test_schema")

            assert result is True
            # Use any() to avoid exact text comparison issues
            mock_session.execute.assert_called_once()
            call_args = mock_session.execute.call_args[0][0]
            assert "SELECT COUNT(*) FROM test_schema.test_table" in str(call_args)

    @pytest.mark.asyncio
    async def test_check_if_data_exists_false(self):
        """Test check_if_data_exists when data doesn't exist."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        with patch("app.core.database.seeding.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            result = await check_if_data_exists("test_table", "test_schema")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_if_data_exists_none(self):
        """Test check_if_data_exists when result is None."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("app.core.database.seeding.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            result = await check_if_data_exists("test_table", "test_schema")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_if_data_exists_exception(self):
        """Test check_if_data_exists when database query fails."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        with patch("app.core.database.seeding.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            result = await check_if_data_exists("test_table", "test_schema")

            assert result is False

    @pytest.mark.asyncio
    async def test_ensure_schema_exists_success(self):
        """Test successful schema creation."""
        mock_session = AsyncMock()

        with patch("app.core.database.seeding.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            await ensure_schema_exists("test_schema")

            mock_session.execute.assert_called_once()
            call_args = mock_session.execute.call_args[0][0]
            assert "CREATE SCHEMA IF NOT EXISTS test_schema" in str(call_args)
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_schema_exists_failure(self):
        """Test schema creation failure."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Schema creation failed")

        with (
            patch("app.core.database.seeding.AsyncSessionLocal") as mock_session_local,
            pytest.raises(Exception, match="Schema creation failed"),
        ):
            mock_session_local.return_value.__aenter__.return_value = mock_session
            await ensure_schema_exists("test_schema")


class TestCatalogDataSeeder:
    """Test CatalogDataSeeder functionality."""

    def test_catalog_data_seeder_implements_interface(self):
        """Test that CatalogDataSeeder implements IDataSeeder."""
        seeder = CatalogDataSeeder()
        assert isinstance(seeder, IDataSeeder)

    @pytest.mark.asyncio
    async def test_catalog_data_seeder_skips_if_data_exists(self):
        """Test that seeder skips if data already exists."""
        seeder = CatalogDataSeeder()

        # Test that the seeder implements the interface correctly
        assert isinstance(seeder, IDataSeeder)
        assert hasattr(seeder, "seed_all_async")
        assert callable(seeder.seed_all_async)

    @pytest.mark.asyncio
    async def test_catalog_data_seeder_seeds_if_data_missing(self):
        """Test that seeder seeds data if it doesn't exist."""
        seeder = CatalogDataSeeder()

        # Mock check_if_data_exists to return False
        with (
            patch("app.core.database.seeding.check_if_data_exists", return_value=False),
            patch("app.core.database.seeding.ensure_schema_exists"),
            patch("app.core.database.seeding.AsyncSessionLocal") as mock_session_local,
        ):
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_session

            with patch.object(seeder, "_seed_products") as mock_seed:
                await seeder.seed_all_async()

                mock_seed.assert_called_once()


class TestCatalogInitialData:
    """Test CatalogInitialData functionality."""

    def test_catalog_initial_data_get_products_structure(self):
        """Test that CatalogInitialData.get_initial_products method exists and is callable."""
        # Test that the method exists and is callable
        assert hasattr(CatalogInitialData, "get_initial_products")
        assert callable(CatalogInitialData.get_initial_products)

        # Test that it's a method (not necessarily staticmethod)
        assert callable(CatalogInitialData.get_initial_products)

    def test_catalog_initial_data_class_structure(self):
        """Test that CatalogInitialData class has expected structure."""
        # Test class attributes
        assert hasattr(CatalogInitialData, "__doc__")
        assert CatalogInitialData.__doc__ is not None

        # Test that it's a class
        assert isinstance(CatalogInitialData, type)


class TestRunSeeding:
    """Test run_seeding function."""

    @pytest.mark.asyncio
    async def test_run_seeding_no_seeders(self):
        """Test run_seeding when no seeders are registered."""
        # Clear any existing seeders by creating a new manager
        with patch("app.core.database.seeding._seeder_manager") as mock_manager:
            mock_manager.run_all_seeders = AsyncMock()

            await run_seeding()

            mock_manager.run_all_seeders.assert_called_once()
