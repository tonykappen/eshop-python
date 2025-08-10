"""Pytest configuration and fixtures for database tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from eshop.core.database.base import Base

# Remove the custom event_loop fixture to avoid pytest-asyncio warning
# pytest-asyncio will handle event loop management automatically


@pytest.fixture
async def mock_db_session():
    """Create a mock database session for testing."""
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock common session methods
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    return mock_session


@pytest.fixture
async def mock_db_engine():
    """Create a mock database engine for testing."""
    mock_engine = AsyncMock()

    # Mock engine methods
    mock_engine.begin = AsyncMock()
    mock_engine.dispose = AsyncMock()

    return mock_engine


@pytest.fixture
def mock_alembic_config():
    """Create mock Alembic configuration for testing."""
    return {
        "script_location": "migrations",
        "sqlalchemy.url": "postgresql+asyncpg://test:test@localhost/test",
        "file_template": "%(rev)s_%(slug)s",
        "version_num_format": "%04d",
    }


@pytest.fixture
def mock_migration_result():
    """Create mock migration result for testing."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Migration completed successfully"
    mock_result.stderr = ""
    return mock_result


@pytest.fixture
def mock_failed_migration_result():
    """Create mock failed migration result for testing."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Migration failed"
    return mock_result


@pytest.fixture
async def test_db_session():
    """Create a test database session using in-memory SQLite."""
    # Create in-memory SQLite engine for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    TestingSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create session
    async with TestingSessionLocal() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "id": "5334c996-8457-4cf0-815c-ed2b77c4ff61",
        "name": "Test Product",
        "category": ["test_category"],
        "description": "Test description",
        "image_file": "test_image.jpg",
        "price": 100.0,
    }


@pytest.fixture
def sample_products_data():
    """Sample products data for testing."""
    return [
        {
            "id": "5334c996-8457-4cf0-815c-ed2b77c4ff61",
            "name": "IPhone X",
            "category": ["category1"],
            "description": "Long description",
            "image_file": "imagefile",
            "price": 500.0,
        },
        {
            "id": "c67d6323-e8b1-4bdf-9a75-b0d0d2e7e914",
            "name": "Samsung 10",
            "category": ["category1"],
            "description": "Long description",
            "image_file": "imagefile",
            "price": 400.0,
        },
    ]


@pytest.fixture
def mock_sql_result():
    """Create mock SQL query result for testing."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    return mock_result


@pytest.fixture
def mock_empty_sql_result():
    """Create mock empty SQL query result for testing."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    return mock_result


@pytest.fixture
def mock_none_sql_result():
    """Create mock None SQL query result for testing."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    return mock_result


# Database test markers
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "migration: mark test as testing migrations"
    )
    config.addinivalue_line(
        "markers", "seeding: mark test as testing seeding"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add database marker to tests that use database fixtures
        if "db_session" in item.fixturenames or "test_db_session" in item.fixturenames:
            item.add_marker(pytest.mark.database)

        # Add migration marker to migration tests
        if "migration" in item.name.lower():
            item.add_marker(pytest.mark.migration)

        # Add seeding marker to seeding tests
        if "seed" in item.name.lower():
            item.add_marker(pytest.mark.seeding)

        # Add integration marker to integration tests
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
