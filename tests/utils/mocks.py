"""Shared mock utilities for tests."""

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import structlog


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


# Logging-specific utilities
def create_mock_logger() -> MagicMock:
    """Create a mock structlog logger for testing."""
    mock_logger = MagicMock(spec=structlog.stdlib.BoundLogger)

    # Mock common logging methods
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger.critical = MagicMock()

    return mock_logger


def create_mock_request(
    method: str = "GET",
    url: str = "http://localhost:8000/test",
    path: str = "/test",
    query_params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    client_ip: str = "127.0.0.1",
    user_agent: str = "test-agent"
) -> MagicMock:
    """Create a mock FastAPI Request object for testing."""
    mock_request = MagicMock()
    mock_request.method = method
    mock_request.url = MagicMock()
    mock_request.url.__str__ = MagicMock(return_value=url)
    mock_request.url.path = path
    mock_request.query_params = query_params or {}
    mock_request.headers = headers or {"user-agent": user_agent}
    mock_request.client = MagicMock()
    mock_request.client.host = client_ip
    mock_request.body = AsyncMock(return_value=b"")

    return mock_request


def create_mock_response(
    status_code: int = 200,
    headers: dict[str, str] | None = None,
    body: bytes | None = None
) -> MagicMock:
    """Create a mock response object for testing."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.headers = headers or {"content-type": "application/json"}
    mock_response.body = body or b'{"status": "ok"}'

    return mock_response


class MockLoggingHandler(logging.Handler):
    """Mock logging handler that captures log records for testing."""

    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)

    def clear(self) -> None:
        """Clear captured records."""
        self.records.clear()

    def get_messages(self, level: str | None = None) -> list[str]:
        """Get log messages, optionally filtered by level."""
        if level:
            return [r.getMessage() for r in self.records if r.levelname == level.upper()]
        return [r.getMessage() for r in self.records]

    def get_records_with_level(self, level: str) -> list[logging.LogRecord]:
        """Get log records with specific level."""
        return [r for r in self.records if r.levelname == level.upper()]


# DI-specific utilities
def create_mock_container() -> MagicMock:
    """Create a mock dependency injection container."""
    mock_container = MagicMock()

    # Mock container methods
    mock_container.wire = MagicMock()
    mock_container.providers = {}
    mock_container.config = MagicMock()
    mock_container.config.from_dict = MagicMock()

    return mock_container


def create_mock_provider(provides: type | None = None, **kwargs) -> MagicMock:
    """Create a mock dependency injection provider."""
    mock_provider = MagicMock()
    mock_provider.provides = provides
    mock_provider.__call__ = MagicMock(return_value=kwargs.get("return_value", MagicMock()))

    return mock_provider


def create_mock_service_class(name: str = "TestService") -> type:
    """Create a mock service class for testing."""
    class MockService:
        def __init__(self, name: str = name):
            self.name = name

        def do_something(self) -> str:
            return f"{self.name} did something"

    return MockService


def create_mock_service_function(name: str = "test_function") -> Any:
    """Create a mock service function for testing."""
    def mock_function(*args, **kwargs) -> str:
        return f"{name} called with {args}, {kwargs}"

    return mock_function


class MockModule:
    """Mock module for testing assembly scanning."""

    def __init__(self, name: str = "test_module"):
        self.__name__ = name
        self.__file__ = f"/path/to/{name}.py"

    def __getattr__(self, name: str) -> Any:
        # Return mock objects for any attribute access
        return MagicMock()
