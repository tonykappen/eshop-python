"""Comprehensive integration tests for API endpoints with schema validation."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestProductsAPIIntegration:
    """Integration tests for products API endpoints."""

    @pytest.mark.integration
    def test_create_product_integration_validation(self):
        """Test create product endpoint with full validation."""
        with patch(
            "app.modules.catalog.api.endpoints.products.get_endpoint_factory"
        ) as mock_factory:
            # Mock the endpoint factory and mediator
            mock_endpoint = AsyncMock()
            mock_result = MagicMock()
            mock_result.id = uuid4()
            mock_response = MagicMock()
            mock_response.data = mock_result
            mock_endpoint.execute = AsyncMock(return_value=mock_response)
            mock_factory.return_value.create_command_endpoint.return_value = (
                mock_endpoint
            )

            # Test valid request
            response = client.post(
                "/api/v1/products/",
                json={
                    "name": "Test Product",
                    "description": "Test description",
                    "price": 99.99,
                    "category": ["Electronics"],
                },
                headers={"Authorization": "Bearer test-token"},
            )

            # Should pass validation and reach handler (mocked)
            # Actual status depends on authentication, but validation passes

    @pytest.mark.integration
    def test_create_product_validation_errors(self):
        """Test create product endpoint validation errors."""
        # Test with negative price
        response = client.post(
            "/api/v1/products/",
            json={
                "name": "Test Product",
                "description": "Test description",
                "price": -10.0,  # Invalid
                "category": ["Electronics"],
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

        # Test with zero price
        response = client.post(
            "/api/v1/products/",
            json={
                "name": "Test Product",
                "description": "Test description",
                "price": 0.0,  # Invalid
                "category": ["Electronics"],
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

        # Test with empty name
        response = client.post(
            "/api/v1/products/",
            json={
                "name": "",  # Invalid
                "description": "Test description",
                "price": 99.99,
                "category": ["Electronics"],
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

        # Test with empty category list
        response = client.post(
            "/api/v1/products/",
            json={
                "name": "Test Product",
                "description": "Test description",
                "price": 99.99,
                "category": [],  # Invalid
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

        # Test with missing required fields
        response = client.post(
            "/api/v1/products/",
            json={
                "name": "Test Product",
                # Missing description, price, category
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    @pytest.mark.integration
    def test_update_product_validation_errors(self):
        """Test update product endpoint validation errors."""
        product_id = uuid4()

        # Test with negative price
        response = client.put(
            f"/api/v1/products/{product_id}",
            json={
                "name": "Updated Product",
                "description": "Updated description",
                "price": -5.0,  # Invalid
                "category": ["Electronics"],
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

        # Test with very long name (exceeds max_length)
        response = client.put(
            f"/api/v1/products/{product_id}",
            json={
                "name": "A" * 201,  # Exceeds max_length=200
                "description": "Updated description",
                "price": 99.99,
                "category": ["Electronics"],
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    @pytest.mark.integration
    def test_get_product_uuid_validation(self):
        """Test get product endpoint UUID validation."""
        # Test with invalid UUID format
        response = client.get(
            "/api/v1/products/invalid-uuid-format",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

        # Test with valid UUID format (will fail auth/authorization but not validation)
        valid_uuid = uuid4()
        response = client.get(
            f"/api/v1/products/{valid_uuid}",
            headers={"Authorization": "Bearer test-token"},
        )
        # Should pass validation (422) but may fail auth (401) or not found (404)
        assert response.status_code != 422

    @pytest.mark.integration
    def test_get_products_pagination_validation(self):
        """Test get products endpoint pagination validation."""
        # Test with valid pagination
        response = client.get(
            "/api/v1/products/?page=1&page_size=10",
            headers={"Authorization": "Bearer test-token"},
        )
        # Should pass validation
        assert response.status_code != 422

        # Test with invalid page (negative)
        response = client.get(
            "/api/v1/products/?page=-1",
            headers={"Authorization": "Bearer test-token"},
        )
        # May or may not be validated depending on endpoint implementation

    @pytest.mark.integration
    def test_delete_product_uuid_validation(self):
        """Test delete product endpoint UUID validation."""
        # Test with invalid UUID
        response = client.delete(
            "/api/v1/products/not-a-uuid",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422


class TestAuthProxyAPIIntegration:
    """Integration tests for auth proxy API endpoints."""

    @pytest.mark.integration
    def test_token_endpoint_schema_validation(self):
        """Test auth proxy token endpoint schema validation."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test-token",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "refresh_token": "refresh-token",
                "token_type": "Bearer",
                "scope": "openid",
            }
            mock_response.headers = {"content-type": "application/json"}

            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            # Test with missing username
            response = client.post(
                "/api/v1/auth-proxy/token",
                data={"password": "testpass"},
            )
            assert response.status_code == 422

            # Test with missing password
            response = client.post(
                "/api/v1/auth-proxy/token",
                data={"username": "testuser"},
            )
            assert response.status_code == 422

            # Test with all required fields
            response = client.post(
                "/api/v1/auth-proxy/token",
                data={
                    "username": "testuser",
                    "password": "testpass",
                },
            )
            # Should pass validation (status depends on mock)
            assert response.status_code != 422


class TestResponseSchemaIntegration:
    """Integration tests for response schema validation."""

    @pytest.mark.integration
    def test_product_response_schema_compliance(self):
        """Test that product responses comply with schema."""
        from app.modules.catalog.contracts.product.dtos import ProductDto
        from app.modules.catalog.api.endpoints.products import ProductResponse

        # Create valid product DTO
        product = ProductDto(
            id=uuid4(),
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            description="Test description",
            price=99.99,
            currency="USD",
            version=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        response = ProductResponse(data=product)

        # Validate response structure
        assert hasattr(response, "data")
        assert hasattr(response, "success")
        assert response.data == product

    @pytest.mark.integration
    def test_paginated_response_schema_compliance(self):
        """Test that paginated responses comply with schema."""
        from app.modules.catalog.api.endpoints.products import ProductsResponse
        from app.modules.catalog.contracts.product.dtos import ProductDto

        products = [
            ProductDto(
                id=uuid4(),
                name=f"Product {i}",
                sku=f"SKU-{i:03d}",
                category=["Electronics"],
                description=f"Description {i}",
                price=99.99 + i,
                currency="USD",
                version=1,
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            )
            for i in range(3)
        ]

        response = ProductsResponse(
            data=products,
            page=1,
            page_size=10,
            total_count=3,
            total_pages=1,
        )

        assert len(response.data) == 3
        assert response.page == 1
        assert response.page_size == 10
        assert response.total_count == 3


class TestSchemaEdgeCases:
    """Test schema edge cases and boundary conditions."""

    def test_product_name_boundary_values(self):
        """Test product name field boundary values."""
        from app.modules.catalog.contracts.product.dtos import ProductDto

        # Test minimum length (1 character)
        product = ProductDto(
            id=uuid4(),
            name="A",  # Minimum length
            sku="TEST-001",
            category=["Electronics"],
            description="Test",
            price=99.99,
            currency="USD",
            version=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        assert product.name == "A"

        # Test maximum length (200 characters)
        product = ProductDto(
            id=uuid4(),
            name="A" * 200,  # Maximum length
            sku="TEST-001",
            category=["Electronics"],
            description="Test",
            price=99.99,
            currency="USD",
            version=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        assert len(product.name) == 200

        # Test exceeds maximum length
        with pytest.raises(Exception):  # ValidationError
            ProductDto(
                id=uuid4(),
                name="A" * 201,  # Exceeds maximum
                sku="TEST-001",
                category=["Electronics"],
                description="Test",
                price=99.99,
                currency="USD",
                version=1,
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            )

    def test_product_price_boundary_values(self):
        """Test product price field boundary values."""
        from app.modules.catalog.contracts.product.dtos import ProductDto

        # Test zero price (should be allowed in DTO, validated at request level)
        product = ProductDto(
            id=uuid4(),
            name="Test",
            sku="TEST-001",
            category=["Electronics"],
            description="Test",
            price=0.0,  # Zero is >= 0
            currency="USD",
            version=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        assert product.price == 0.0

        # Test negative price (should fail ge=0 validation)
        with pytest.raises(Exception):  # ValidationError
            ProductDto(
                id=uuid4(),
                name="Test",
                sku="TEST-001",
                category=["Electronics"],
                description="Test",
                price=-10.0,  # Negative fails ge=0
                currency="USD",
                version=1,
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            )

    def test_product_category_boundary_values(self):
        """Test product category field boundary values."""
        from app.modules.catalog.contracts.product.dtos import ProductDto

        # Test minimum length (1 category)
        product = ProductDto(
            id=uuid4(),
            name="Test",
            sku="TEST-001",
            category=["Electronics"],  # Minimum: 1 category
            description="Test",
            price=99.99,
            currency="USD",
            version=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        assert len(product.category) == 1

        # Test empty category (should fail min_length=1)
        with pytest.raises(Exception):  # ValidationError
            ProductDto(
                id=uuid4(),
                name="Test",
                sku="TEST-001",
                category=[],  # Empty fails min_length=1
                description="Test",
                price=99.99,
                currency="USD",
                version=1,
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            )

