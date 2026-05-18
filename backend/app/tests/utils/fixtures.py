"""Shared pytest fixtures for tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.core.auth.keycloak import KeycloakUser
from app.tests.utils.mocks import MockKeycloakService, create_mock_settings


@pytest.fixture
def mock_settings() -> MagicMock:
    """Provide mock settings for tests."""
    return create_mock_settings()


@pytest.fixture
def mock_keycloak_service() -> MockKeycloakService:
    """Provide mock Keycloak service for tests."""
    return MockKeycloakService()


@pytest.fixture
def mock_keycloak_user() -> KeycloakUser:
    """Provide mock Keycloak user for tests."""
    return KeycloakUser(
        sub="test-user-id",
        preferred_username="testuser",
        email="test@example.com",
        roles=["user"],
    )


@pytest.fixture
def mock_async_session() -> Generator[AsyncMock, None, None]:
    """Provide mock async database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    yield session


@pytest.fixture
def mock_engine() -> MagicMock:
    """Provide mock database engine."""
    engine = MagicMock()
    engine.begin = MagicMock()
    engine.dispose = MagicMock()
    return engine


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Provide mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.exists = AsyncMock()
    return client


@pytest.fixture
def mock_rabbitmq_connection() -> AsyncMock:
    """Provide mock RabbitMQ connection."""
    connection = AsyncMock()
    connection.close = AsyncMock()
    return connection
