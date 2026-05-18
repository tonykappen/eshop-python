"""Tests for ordering presentation endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.main import app
from fastapi.testclient import TestClient


class TestOrderEndpoints:
    """Test ordering HTTP endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_token(self):
        """Create mock JWT token."""
        return "Bearer mock_jwt_token"

    @pytest.fixture
    def sample_order_data(self):
        """Sample order data for testing."""
        order_id = uuid4()
        customer_id = uuid4()
        product_id = uuid4()

        return {
            "order": {
                "id": str(order_id),
                "customer_id": str(customer_id),
                "order_name": "Test Order",
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email_address": "john@example.com",
                    "address_line": "123 Main St",
                    "country": "USA",
                    "state": "CA",
                    "zip_code": "12345",
                },
                "billing_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email_address": "john@example.com",
                    "address_line": "123 Main St",
                    "country": "USA",
                    "state": "CA",
                    "zip_code": "12345",
                },
                "payment": {
                    "card_name": "John Doe",
                    "card_number": "1234567890123456",
                    "expiration": "12/25",
                    "cvv": "123",
                    "payment_method": 1,
                },
                "items": [
                    {
                        "order_id": str(order_id),
                        "product_id": str(product_id),
                        "quantity": 2,
                        "price": "99.99",
                    }
                ],
            }
        }

    def test_create_order_endpoint(self, client, mock_token, sample_order_data):
        """Test create order endpoint."""
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch(
                "app.modules.ordering.utils.get_endpoint_factory"
            ) as mock_get_factory,
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
                "/api/v1/orders/",
                json=sample_order_data,
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data

    def test_get_order_by_id_endpoint(self, client, mock_token):
        """Test get order by ID endpoint."""
        order_id = str(uuid4())
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch(
                "app.modules.ordering.utils.get_endpoint_factory"
            ) as mock_get_factory,
        ):
            mock_mediator = AsyncMock()
            mock_order_dto = MagicMock()
            mock_order_dto.id = uuid4()
            mock_order_dto.customer_id = uuid4()
            mock_order_dto.order_name = "Test Order"
            mock_order_dto.items = []
            mock_result = MagicMock()
            mock_result.order = mock_order_dto
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
                f"/api/v1/orders/{order_id}",
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 200
            data = response.json()
            assert "order" in data

    def test_get_orders_endpoint(self, client, mock_token):
        """Test get orders endpoint."""
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch(
                "app.modules.ordering.utils.get_endpoint_factory"
            ) as mock_get_factory,
        ):
            mock_mediator = AsyncMock()
            mock_paginated_result = MagicMock()
            mock_paginated_result.items = []
            mock_paginated_result.total = 0
            mock_paginated_result.page = 1
            mock_paginated_result.size = 10
            mock_result = MagicMock()
            mock_result.orders = mock_paginated_result
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
                "/api/v1/orders/",
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 200
            data = response.json()
            assert "orders" in data

    def test_get_orders_with_pagination(self, client, mock_token):
        """Test get orders endpoint with pagination."""
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch(
                "app.modules.ordering.utils.get_endpoint_factory"
            ) as mock_get_factory,
        ):
            mock_mediator = AsyncMock()
            mock_paginated_result = MagicMock()
            mock_paginated_result.items = []
            mock_paginated_result.total = 0
            mock_paginated_result.page = 2
            mock_paginated_result.size = 5
            mock_result = MagicMock()
            mock_result.orders = mock_paginated_result
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
                "/api/v1/orders/?page_index=1&page_size=5",
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 200
            data = response.json()
            assert "orders" in data

    def test_delete_order_endpoint(self, client, mock_token):
        """Test delete order endpoint."""
        order_id = str(uuid4())
        with (
            patch(
                "app.core.mediator.fastapi_integration.get_mediator"
            ) as mock_get_mediator,
            patch(
                "app.modules.ordering.utils.get_endpoint_factory"
            ) as mock_get_factory,
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
                f"/api/v1/orders/{order_id}",
                headers={"Authorization": mock_token},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_success"] is True
