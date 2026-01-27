"""Tests for basket presentation endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestBasketEndpoints:
    """Test basket HTTP endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_token(self):
        """Create mock JWT token."""
        return "Bearer mock_jwt_token"

    @pytest.fixture
    def sample_basket_data(self):
        """Sample basket data for testing."""
        return {
            "shopping_cart": {
                "id": str(uuid4()),
                "user_name": "testuser",
                "items": [],
            }
        }

    @pytest.fixture
    def sample_basket_item_data(self):
        """Sample basket item data for testing."""
        return {
            "shopping_cart_item": {
                "id": str(uuid4()),
                "shopping_cart_id": str(uuid4()),
                "product_id": str(uuid4()),
                "quantity": 2,
                "color": "Red",
                "price": "99.99",
                "product_name": "Test Product",
            }
        }

    @pytest.fixture
    def sample_checkout_data(self):
        """Sample checkout data for testing."""
        return {
            "basket_checkout": {
                "user_name": "testuser",
                "customer_id": str(uuid4()),
                "total_price": "199.98",
                "first_name": "John",
                "last_name": "Doe",
                "email_address": "john@example.com",
                "address_line": "123 Main St",
                "country": "USA",
                "state": "CA",
                "zip_code": "12345",
                "card_name": "John Doe",
                "card_number": "1234567890123456",
                "expiration": "12/25",
                "cvv": "123",
                "payment_method": 1,
            }
        }

    def test_create_basket_endpoint(self, client, mock_token, sample_basket_data):
        """Test create basket endpoint."""
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch("app.modules.basket.utils.get_endpoint_factory") as mock_get_factory,
        ):
            mock_mediator = AsyncMock()
            mock_result = MagicMock()
            mock_result.id = uuid4()
            mock_mediator.send.return_value = mock_result
            mock_get_mediator.return_value = mock_mediator

            mock_factory = MagicMock()
            mock_endpoint = AsyncMock()
            mock_response = MagicMock()
            mock_response.data = mock_result
            mock_endpoint.execute.return_value = mock_response
            mock_factory.create_command_endpoint.return_value = mock_endpoint
            mock_get_factory.return_value = mock_factory

            response = client.post(
                "/api/v1/basket/",
                json=sample_basket_data,
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data

    def test_get_basket_endpoint(self, client, mock_token):
        """Test get basket endpoint."""
        user_name = "testuser"
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch("app.modules.basket.utils.get_endpoint_factory") as mock_get_factory,
        ):
            mock_mediator = AsyncMock()
            mock_basket_dto = MagicMock()
            mock_basket_dto.id = uuid4()
            mock_basket_dto.user_name = user_name
            mock_basket_dto.items = []
            mock_result = MagicMock()
            mock_result.shopping_cart = mock_basket_dto
            mock_mediator.send.return_value = mock_result
            mock_get_mediator.return_value = mock_mediator

            mock_factory = MagicMock()
            mock_endpoint = AsyncMock()
            mock_response = MagicMock()
            mock_response.data = mock_result
            mock_endpoint.execute.return_value = mock_response
            mock_factory.create_query_endpoint.return_value = mock_endpoint
            mock_get_factory.return_value = mock_factory

            response = client.get(
                f"/api/v1/basket/{user_name}",
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 200
            data = response.json()
            assert "shopping_cart" in data

    def test_add_item_endpoint(self, client, mock_token, sample_basket_item_data):
        """Test add item endpoint."""
        user_name = "testuser"
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch("app.modules.basket.utils.get_endpoint_factory") as mock_get_factory,
        ):
            mock_mediator = AsyncMock()
            mock_result = MagicMock()
            mock_result.id = uuid4()
            mock_mediator.send.return_value = mock_result
            mock_get_mediator.return_value = mock_mediator

            mock_factory = MagicMock()
            mock_endpoint = AsyncMock()
            mock_response = MagicMock()
            mock_response.data = mock_result
            mock_endpoint.execute.return_value = mock_response
            mock_factory.create_command_endpoint.return_value = mock_endpoint
            mock_get_factory.return_value = mock_factory

            response = client.post(
                f"/api/v1/basket/{user_name}/items",
                json=sample_basket_item_data,
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data

    def test_remove_item_endpoint(self, client, mock_token):
        """Test remove item endpoint."""
        user_name = "testuser"
        product_id = str(uuid4())
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch("app.modules.basket.utils.get_endpoint_factory") as mock_get_factory,
        ):
            mock_mediator = AsyncMock()
            mock_result = MagicMock()
            mock_result.id = uuid4()
            mock_mediator.send.return_value = mock_result
            mock_get_mediator.return_value = mock_mediator

            mock_factory = MagicMock()
            mock_endpoint = AsyncMock()
            mock_response = MagicMock()
            mock_response.data = mock_result
            mock_endpoint.execute.return_value = mock_response
            mock_factory.create_command_endpoint.return_value = mock_endpoint
            mock_get_factory.return_value = mock_factory

            response = client.delete(
                f"/api/v1/basket/{user_name}/items/{product_id}",
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 200
            data = response.json()
            assert "id" in data

    def test_delete_basket_endpoint(self, client, mock_token):
        """Test delete basket endpoint."""
        user_name = "testuser"
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch("app.modules.basket.utils.get_endpoint_factory") as mock_get_factory,
        ):
            mock_mediator = AsyncMock()
            mock_result = MagicMock()
            mock_result.is_success = True
            mock_mediator.send.return_value = mock_result
            mock_get_mediator.return_value = mock_mediator

            mock_factory = MagicMock()
            mock_endpoint = AsyncMock()
            mock_response = MagicMock()
            mock_response.data = mock_result
            mock_endpoint.execute.return_value = mock_response
            mock_factory.create_command_endpoint.return_value = mock_endpoint
            mock_get_factory.return_value = mock_factory

            response = client.delete(
                f"/api/v1/basket/{user_name}",
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_success"] is True

    def test_checkout_basket_endpoint(self, client, mock_token, sample_checkout_data):
        """Test checkout basket endpoint."""
        user_name = "testuser"
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch("app.modules.basket.utils.get_endpoint_factory") as mock_get_factory,
        ):
            mock_mediator = AsyncMock()
            mock_result = MagicMock()
            mock_result.is_success = True
            mock_mediator.send.return_value = mock_result
            mock_get_mediator.return_value = mock_mediator

            mock_factory = MagicMock()
            mock_endpoint = AsyncMock()
            mock_response = MagicMock()
            mock_response.data = mock_result
            mock_endpoint.execute.return_value = mock_response
            mock_factory.create_command_endpoint.return_value = mock_endpoint
            mock_get_factory.return_value = mock_factory

            response = client.post(
                f"/api/v1/basket/{user_name}/checkout",
                json=sample_checkout_data,
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_success"] is True
