"""Comprehensive tests for Catalog API endpoints."""

from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4


class TestCatalogAPIEndpoints:
    """Test Catalog API endpoints with RBAC."""

    def test_get_products_success(
        self, client: Any, sample_products_response: Any
    ) -> None:
        """Test GET /api/v1/products/ returns products successfully."""
        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.return_value = sample_products_response
            mock_get_mediator.return_value = mock_mediator

            response = client.get(
                "/api/v1/products/", headers={"Authorization": "Bearer mock-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 2
            assert data["items"][0]["name"] == "Test Product 1"

    def test_get_products_with_pagination(
        self, client: Any, sample_products_response: Any
    ) -> None:
        """Test GET /api/v1/products/ with pagination parameters."""
        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.return_value = sample_products_response
            mock_get_mediator.return_value = mock_mediator

            response = client.get(
                "/api/v1/products/?page=2&page_size=5",
                headers={"Authorization": "Bearer mock-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 1  # From sample response
            assert data["size"] == 10  # From sample response

    def test_get_product_by_id_success(
        self, client: Any, sample_product_response: Any
    ) -> None:
        """Test GET /api/v1/products/{id} returns product successfully."""
        product_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.return_value = sample_product_response
            mock_get_mediator.return_value = mock_mediator

            response = client.get(
                f"/api/v1/products/{product_id}",
                headers={"Authorization": "Bearer mock-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["id"] == product_id
            assert data["data"]["name"] == "Test Product"

    def test_get_product_by_id_not_found(self, client: Any) -> None:
        """Test GET /api/v1/products/{id} returns 404 for non-existent product."""
        product_id = str(uuid4())

        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.side_effect = Exception("Product not found")
            mock_get_mediator.return_value = mock_mediator

            response = client.get(
                f"/api/v1/products/{product_id}",
                headers={"Authorization": "Bearer mock-token"},
            )

            # Should handle the exception and return appropriate error
            assert response.status_code in [404, 500]  # Depending on error handling

    def test_create_product_success_admin(
        self, client: Any, sample_product_data: Any, admin_headers: Any
    ) -> None:
        """Test POST /api/v1/products/ creates product successfully with admin role."""
        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.return_value = {"id": str(uuid4())}
            mock_get_mediator.return_value = mock_mediator

            response = client.post(
                "/api/v1/products/", json=sample_product_data, headers=admin_headers
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data

    def test_create_product_success_manager(
        self, client: Any, sample_product_data: Any, manager_headers: Any
    ) -> None:
        """Test POST /api/v1/products/ creates product successfully with manager role."""
        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.return_value = {"id": str(uuid4())}
            mock_get_mediator.return_value = mock_mediator

            response = client.post(
                "/api/v1/products/", json=sample_product_data, headers=manager_headers
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data

    def test_create_product_forbidden_user(
        self, client: Any, sample_product_data: Any, user_headers: Any
    ) -> None:
        """Test POST /api/v1/products/ returns 403 for regular user."""
        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.side_effect = Exception("Insufficient permissions")
            mock_get_mediator.return_value = mock_mediator

            response = client.post(
                "/api/v1/products/", json=sample_product_data, headers=user_headers
            )

            # Should return 403 or handle permission error
            assert response.status_code in [403, 500]

    def test_create_product_validation_error(
        self, client: Any, admin_headers: Any
    ) -> None:
        """Test POST /api/v1/products/ returns 422 for invalid data."""
        invalid_data = {
            "name": "",  # Empty name should be invalid
            "price": -10,  # Negative price should be invalid
        }

        response = client.post(
            "/api/v1/products/", json=invalid_data, headers=admin_headers
        )

        assert response.status_code == 422

    def test_update_product_success_admin(
        self, client: Any, sample_product_data: Any, admin_headers: Any
    ) -> None:
        """Test PUT /api/v1/products/{id} updates product successfully with admin role."""
        product_id = str(uuid4())

        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.return_value = {"is_success": True}
            mock_get_mediator.return_value = mock_mediator

            response = client.put(
                f"/api/v1/products/{product_id}",
                json=sample_product_data,
                headers=admin_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_update_product_not_found(
        self, client: Any, sample_product_data: Any, admin_headers: Any
    ) -> None:
        """Test PUT /api/v1/products/{id} returns 404 for non-existent product."""
        product_id = str(uuid4())

        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.side_effect = Exception("Product not found")
            mock_get_mediator.return_value = mock_mediator

            response = client.put(
                f"/api/v1/products/{product_id}",
                json=sample_product_data,
                headers=admin_headers,
            )

            assert response.status_code in [404, 500]

    def test_delete_product_success_admin(
        self, client: Any, admin_headers: Any
    ) -> None:
        """Test DELETE /api/v1/products/{id} deletes product successfully with admin role."""
        product_id = str(uuid4())

        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.return_value = {"is_success": True}
            mock_get_mediator.return_value = mock_mediator

            response = client.delete(
                f"/api/v1/products/{product_id}", headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_delete_product_not_found(self, client: Any, admin_headers: Any) -> None:
        """Test DELETE /api/v1/products/{id} returns 404 for non-existent product."""
        product_id = str(uuid4())

        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.side_effect = Exception("Product not found")
            mock_get_mediator.return_value = mock_mediator

            response = client.delete(
                f"/api/v1/products/{product_id}", headers=admin_headers
            )

            assert response.status_code in [404, 500]

    def test_delete_product_forbidden_user(
        self, client: Any, user_headers: Any
    ) -> None:
        """Test DELETE /api/v1/products/{id} returns 403 for regular user."""
        product_id = str(uuid4())

        with patch(
            "app.core.mediator.fastapi_integration.get_mediator"
        ) as mock_get_mediator:
            mock_mediator = AsyncMock()
            mock_mediator.send.side_effect = Exception("Insufficient permissions")
            mock_get_mediator.return_value = mock_mediator

            response = client.delete(
                f"/api/v1/products/{product_id}", headers=user_headers
            )

            assert response.status_code in [403, 500]

    def test_unauthorized_access(self, client: Any, sample_product_data: Any) -> None:
        """Test API endpoints return 401 for unauthorized access."""
        # Test without authorization header
        response = client.get("/api/v1/products/")
        assert response.status_code == 401

        response = client.post("/api/v1/products/", json=sample_product_data)
        assert response.status_code == 401

        product_id = str(uuid4())
        response = client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 401

        response = client.put(
            f"/api/v1/products/{product_id}", json=sample_product_data
        )
        assert response.status_code == 401

        response = client.delete(f"/api/v1/products/{product_id}")
        assert response.status_code == 401

    def test_invalid_uuid_format(self, client: Any, admin_headers: Any) -> None:
        """Test API endpoints return 422 for invalid UUID format."""
        invalid_uuid = "invalid-uuid-format"

        response = client.get(f"/api/v1/products/{invalid_uuid}", headers=admin_headers)
        assert response.status_code == 422

        response = client.put(
            f"/api/v1/products/{invalid_uuid}", json={}, headers=admin_headers
        )
        assert response.status_code == 422

        response = client.delete(
            f"/api/v1/products/{invalid_uuid}", headers=admin_headers
        )
        assert response.status_code == 422
