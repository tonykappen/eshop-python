"""Test configuration and utilities for Catalog module tests."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.database.session import AsyncSessionLocal
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import SqlProductRepository as ProductRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    return session


@pytest.fixture
def mock_product_repository():
    """Mock ProductRepository for testing."""
    repository = AsyncMock(spec=ProductRepository)
    repository.create = AsyncMock()
    repository.get_by_id = AsyncMock()
    repository.get_paginated = AsyncMock()
    repository.update = AsyncMock()
    repository.delete = AsyncMock()
    repository.exists = AsyncMock()
    return repository


@pytest.fixture
def mock_mediator():
    """Mock Mediator for testing."""
    mediator = AsyncMock()
    mediator.send = AsyncMock()
    mediator.register_handler = AsyncMock()
    mediator.unregister_handler = AsyncMock()
    return mediator


@pytest.fixture
def mock_endpoint_factory():
    """Mock CQRSEndpointFactory for testing."""
    factory = MagicMock()
    factory.create_command_endpoint = MagicMock()
    factory.create_query_endpoint = MagicMock()
    return factory


@pytest.fixture
def sample_product_entity():
    """Sample product entity for testing."""
    from app.modules.catalog.infrastructure.models.product_orm import ProductORM
    from decimal import Decimal
    from uuid import uuid4
    
    product = MagicMock(spec=ProductORM)
    product.id = uuid4()
    product.name = "Test Product"
    product.description = "Test Description"
    product.price = Decimal("99.99")
    product.image_file = "test.jpg"
    product.category = ["Electronics"]
    return product


@pytest.fixture
def sample_product_dto():
    """Sample ProductDto for testing."""
    from app.modules.catalog.application.public_interface.dto.product import ProductDto
    from decimal import Decimal
    from uuid import uuid4
    
    return ProductDto(
        id=uuid4(),
        name="Test Product",
        description="Test Description",
        price=Decimal("99.99"),
        picture_url="test.jpg",
        category=["Electronics"]
    )


@pytest.fixture
def mock_auth_headers():
    """Mock authentication headers for testing."""
    return {
        "admin": {
            "Authorization": "Bearer mock-admin-token",
            "Content-Type": "application/json"
        },
        "manager": {
            "Authorization": "Bearer mock-manager-token",
            "Content-Type": "application/json"
        },
        "user": {
            "Authorization": "Bearer mock-user-token",
            "Content-Type": "application/json"
        }
    }


@pytest.fixture
def mock_keycloak_user():
    """Mock Keycloak user for testing."""
    from app.core.auth.keycloak import KeycloakUser
    
    return KeycloakUser(
        sub="test-user-id",
        preferred_username="testuser",
        email="test@example.com",
        roles=["user"]
    )


@pytest.fixture
def mock_keycloak_admin():
    """Mock Keycloak admin user for testing."""
    from app.core.auth.keycloak import KeycloakUser
    
    return KeycloakUser(
        sub="test-admin-id",
        preferred_username="adminuser",
        email="admin@example.com",
        roles=["admin", "manager", "user"]
    )


@pytest.fixture
def mock_keycloak_manager():
    """Mock Keycloak manager user for testing."""
    from app.core.auth.keycloak import KeycloakUser
    
    return KeycloakUser(
        sub="test-manager-id",
        preferred_username="manager",
        email="manager@example.com",
        roles=["manager", "user"]
    )


@pytest.fixture
def mock_async_session_local():
    """Mock AsyncSessionLocal for testing."""
    with patch('app.modules.catalog.application.features.products.commands.create_product.handler.AsyncSessionLocal') as mock:
        mock_session = AsyncMock()
        mock.return_value.__aenter__.return_value = mock_session
        mock.return_value.__aexit__.return_value = None
        yield mock


@pytest.fixture
def mock_product_repository_class():
    """Mock ProductRepository class for testing."""
    with patch('app.modules.catalog.application.features.products.commands.create_product.handler.ProductRepository') as mock:
        mock_repo = AsyncMock(spec=ProductRepository)
        mock.return_value = mock_repo
        yield mock_repo


@pytest.fixture
def mock_cancellation_token():
    """Mock CancellationToken for testing."""
    token = MagicMock()
    token.throw_if_cancellation_requested = MagicMock()
    return token


@pytest.fixture
def sample_pagination_data():
    """Sample pagination data for testing."""
    from app.core.pagination.models import PaginatedResult
    from decimal import Decimal
    from uuid import uuid4
    
    products = [
        {
            "id": str(uuid4()),
            "name": f"Product {i}",
            "description": f"Description {i}",
            "price": str(Decimal("99.99") + i),
            "picture_url": f"image{i}.jpg",
            "category": ["Electronics"]
        }
        for i in range(5)
    ]
    
    return PaginatedResult(
        items=products,
        total=5,
        page=1,
        page_size=10,
        total_pages=1
    )


@pytest.fixture
def mock_http_request():
    """Mock HTTP request for testing."""
    from fastapi import Request
    from unittest.mock import MagicMock
    
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer mock-token"}
    request.url = MagicMock()
    request.url.path = "/api/v1/products/"
    return request


@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI app for testing."""
    from fastapi import FastAPI
    from unittest.mock import MagicMock
    
    app = MagicMock(spec=FastAPI)
    app.state = MagicMock()
    app.state.container = MagicMock()
    return app


# Test data fixtures
@pytest.fixture
def valid_product_data():
    """Valid product data for testing."""
    return {
        "name": "Valid Test Product",
        "description": "A valid product for testing",
        "price": 199.99,
        "picture_url": "https://example.com/valid.jpg",
        "category": ["Electronics", "Testing"]
    }


@pytest.fixture
def invalid_product_data():
    """Invalid product data for testing."""
    return {
        "name": "",  # Empty name
        "description": "Invalid product",
        "price": -100,  # Negative price
        "picture_url": "invalid-url",
        "category": "not_a_list"  # Should be a list
    }


@pytest.fixture
def edge_case_product_data():
    """Edge case product data for testing."""
    return {
        "name": "Edge Case Product with Special Ch@rs! 🚀",
        "description": "A" * 1000,  # Very long description
        "price": 0.01,  # Very small price
        "picture_url": "https://example.com/" + "a" * 1000 + ".jpg",  # Very long URL
        "category": [f"Category{i}" for i in range(100)]  # Many categories
    }


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ.update({
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
        "REDIS_URL": "redis://localhost:6379",
        "RABBITMQ_URL": "amqp://guest:guest@localhost:5672/",
        "KEYCLOAK_SERVER_URL": "http://localhost:8080",
        "KEYCLOAK_CLIENT_ID": "test-client",
        "KEYCLOAK_CLIENT_SECRET": "test-secret",
        "ENVIRONMENT": "test"
    })
    yield
    # Cleanup after test
    for key in ["DATABASE_URL", "REDIS_URL", "RABBITMQ_URL", "KEYCLOAK_SERVER_URL", "ENVIRONMENT"]:
        os.environ.pop(key, None)


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring authentication"
    )
    config.addinivalue_line(
        "markers", "rbac: mark test as testing RBAC functionality"
    )



