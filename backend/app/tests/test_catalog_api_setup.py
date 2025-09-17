"""Test setup and configuration for Catalog API tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.mediator.mediator import Mediator
from app.core.mediator.handler_registry import HandlerRegistry
from app.core.di.container import Container


@pytest.fixture
def mock_mediator():
    """Create a mock mediator for testing."""
    mediator = AsyncMock(spec=Mediator)
    mediator.send = AsyncMock()
    mediator.register_handler = AsyncMock()
    mediator.unregister_handler = AsyncMock()
    return mediator


@pytest.fixture
def mock_handler_registry():
    """Create a mock handler registry for testing."""
    registry = AsyncMock(spec=HandlerRegistry)
    registry.register = AsyncMock()
    registry.unregister = AsyncMock()
    registry.get_handler = AsyncMock()
    return registry


@pytest.fixture
def mock_container():
    """Create a mock container for testing."""
    container = MagicMock(spec=Container)
    container.get = MagicMock()
    return container


@pytest.fixture
def configured_app(mock_mediator, mock_handler_registry, mock_container):
    """Create a FastAPI app with mocked dependencies."""
    # Mock the mediator configuration
    with patch('app.core.mediator.fastapi_integration.get_mediator') as mock_get_mediator:
        mock_get_mediator.return_value = mock_mediator
        
        # Mock the container
        with patch('app.core.di.container.get_container') as mock_get_container:
            mock_get_container.return_value = mock_container
            
            # Mock the handler registry
            with patch('app.core.mediator.handler_registry.get_handler_registry') as mock_get_registry:
                mock_get_registry.return_value = mock_handler_registry
                
                yield app


@pytest.fixture
def client(configured_app):
    """Create test client with configured app."""
    return TestClient(configured_app)


@pytest.fixture
async def async_client(configured_app):
    """Create async test client with configured app."""
    async with AsyncClient(app=configured_app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_product_response():
    """Sample product response for testing."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Test Product",
        "description": "A test product",
        "price": 99.99,
        "picture_url": "https://example.com/image.jpg",
        "category": ["Electronics"]
    }


@pytest.fixture
def sample_products_response():
    """Sample products list response for testing."""
    return {
        "items": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Test Product 1",
                "description": "A test product 1",
                "price": 99.99,
                "picture_url": "https://example.com/image1.jpg",
                "category": ["Electronics"]
            },
            {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Test Product 2",
                "description": "A test product 2",
                "price": 149.99,
                "picture_url": "https://example.com/image2.jpg",
                "category": ["Gadgets"]
            }
        ],
        "total": 2,
        "page": 1,
        "size": 10,
        "pages": 1
    }


@pytest.fixture
def admin_headers():
    """Admin user headers for testing."""
    return {
        "Authorization": "Bearer mock-admin-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def manager_headers():
    """Manager user headers for testing."""
    return {
        "Authorization": "Bearer mock-manager-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def user_headers():
    """Regular user headers for testing."""
    return {
        "Authorization": "Bearer mock-user-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "description": "A test product description",
        "price": 99.99,
        "picture_url": "https://example.com/image.jpg",
        "category": ["Electronics", "Gadgets"]
    }

