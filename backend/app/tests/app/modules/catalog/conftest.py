"""Catalog module test fixtures."""

import pytest
from app.core.database.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def test_db_session():
    """Create a test database session using in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    testing_session_local = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with testing_session_local() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_product_data():
    """Sample product data for catalog tests."""
    return {
        "id": "5334c996-8457-4cf0-815c-ed2b77c4ff61",
        "name": "Test Product",
        "category": ["test_category"],
        "description": "Test description",
        "image_file": "test_image.jpg",
        "price": 100.0,
    }
