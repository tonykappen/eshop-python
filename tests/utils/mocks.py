"""Shared mock utilities for tests."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockKeycloakService:
    """Mock Keycloak service for testing."""

    def __init__(self, initialized: bool = True):
        self._initialized = initialized
        self.keycloak = MagicMock()
        self.get_user_info = AsyncMock()
        self.check_role = AsyncMock()
        self.health_check = AsyncMock()

    @property
    def initialized(self) -> bool:
        return self._initialized


class MockKeycloakUser:
    """Mock Keycloak user for testing."""

    def __init__(
        self,
        sub: str = "test-user-id",
        preferred_username: str = "testuser",
        email: str = "test@example.com",
        roles: list[str] | None = None,
        **kwargs
    ):
        self.sub = sub
        self.preferred_username = preferred_username
        self.email = email
        self.roles = roles or ["user"]
        for key, value in kwargs.items():
            setattr(self, key, value)


def create_mock_settings(**overrides) -> MagicMock:
    """Create mock settings with optional overrides."""
    settings = MagicMock()

    # Default values
    settings.keycloak_server_url = "http://localhost:8080"
    settings.keycloak_realm = "eshop"
    settings.keycloak_client_id = "eshop-api"
    settings.keycloak_client_secret = "your-client-secret"
    settings.keycloak_callback_uri = "http://localhost:8000/callback"

    # Apply overrides
    for key, value in overrides.items():
        setattr(settings, key, value)

    return settings


def create_mock_async_client(
    status_code: int = 200,
    response_data: dict[str, Any] | None = None,
    side_effect: Exception | None = None
) -> AsyncMock:
    """Create mock async HTTP client."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    if side_effect:
        mock_client.get.side_effect = side_effect
    else:
        mock_response.status_code = status_code
        if response_data:
            mock_response.json.return_value = response_data
        mock_client.get.return_value = mock_response

    return mock_client


def create_mock_fastapi_keycloak(**overrides) -> MagicMock:
    """Create mock FastAPI Keycloak instance."""
    mock_keycloak = MagicMock()

    # Default methods
    mock_keycloak.get_user = AsyncMock()
    mock_keycloak.get_current_user = AsyncMock()
    mock_keycloak.get_current_user_optional = AsyncMock()

    # Apply overrides
    for key, value in overrides.items():
        setattr(mock_keycloak, key, value)

    return mock_keycloak
