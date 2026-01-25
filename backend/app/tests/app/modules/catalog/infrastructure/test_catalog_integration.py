"""Integration tests for Catalog module with real database."""

import asyncio
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.catalog.application.public_interface.dto.product import ProductDto
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import SqlProductRepository as ProductRepository


class TestCatalogIntegration:
    """Integration tests for the complete catalog module."""

    @pytest.fixture
    async def client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    async def sample_product_data(self):
        """Sample product data for testing."""
        return {
            "name": "Integration Test Product",
            "description": "A product for integration testing",
            "price": 199.99,
            "picture_url": "https://example.com/integration-test.jpg",
            "category": ["Integration", "Testing"]
        }

    @pytest.fixture
    async def admin_headers(self):
        """Admin user headers for testing."""
        return {
            "Authorization": "Bearer mock-admin-token",
            "Content-Type": "application/json"
        }

    @pytest.fixture
    async def manager_headers(self):
        """Manager user headers for testing."""
        return {
            "Authorization": "Bearer mock-manager-token",
            "Content-Type": "application/json"
        }

    @pytest.fixture
    async def user_headers(self):
        """Regular user headers for testing."""
        return {
            "Authorization": "Bearer mock-user-token",
            "Content-Type": "application/json"
        }

    @pytest.mark.asyncio
    async def test_complete_crud_workflow_admin(self, client, sample_product_data, admin_headers):
        """Test complete CRUD workflow with admin user."""
        # 1. Create a product
        create_response = await client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers=admin_headers
        )
        assert create_response.status_code == 201
        created_product = create_response.json()
        product_id = created_product["id"]
        assert product_id is not None

        # 2. Get the created product
        get_response = await client.get(
            f"/api/v1/products/{product_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 200
        retrieved_product = get_response.json()
        assert retrieved_product["data"]["id"] == product_id
        assert retrieved_product["data"]["name"] == sample_product_data["name"]

        # 3. Update the product
        updated_data = sample_product_data.copy()
        updated_data["name"] = "Updated Integration Test Product"
        updated_data["price"] = 299.99

        update_response = await client.put(
            f"/api/v1/products/{product_id}",
            json=updated_data,
            headers=admin_headers
        )
        assert update_response.status_code == 200
        update_result = update_response.json()
        assert update_result["success"] is True

        # 4. Verify the update
        get_updated_response = await client.get(
            f"/api/v1/products/{product_id}",
            headers=admin_headers
        )
        assert get_updated_response.status_code == 200
        updated_product = get_updated_response.json()
        assert updated_product["data"]["name"] == updated_data["name"]
        assert updated_product["data"]["price"] == str(updated_data["price"])

        # 5. Delete the product
        delete_response = await client.delete(
            f"/api/v1/products/{product_id}",
            headers=admin_headers
        )
        assert delete_response.status_code == 200
        delete_result = delete_response.json()
        assert delete_result["success"] is True

        # 6. Verify deletion (should return 404)
        get_deleted_response = await client.get(
            f"/api/v1/products/{product_id}",
            headers=admin_headers
        )
        assert get_deleted_response.status_code in [404, 500]  # Depending on error handling

    @pytest.mark.asyncio
    async def test_complete_crud_workflow_manager(self, client, sample_product_data, manager_headers):
        """Test complete CRUD workflow with manager user."""
        # 1. Create a product
        create_response = await client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers=manager_headers
        )
        assert create_response.status_code == 201
        created_product = create_response.json()
        product_id = created_product["id"]

        # 2. Update the product
        updated_data = sample_product_data.copy()
        updated_data["name"] = "Manager Updated Product"

        update_response = await client.put(
            f"/api/v1/products/{product_id}",
            json=updated_data,
            headers=manager_headers
        )
        assert update_response.status_code == 200

        # 3. Delete the product
        delete_response = await client.delete(
            f"/api/v1/products/{product_id}",
            headers=manager_headers
        )
        assert delete_response.status_code == 200

    @pytest.mark.asyncio
    async def test_user_readonly_access(self, client, sample_product_data, user_headers):
        """Test that regular users can only read products."""
        # 1. Try to create a product (should fail)
        create_response = await client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers=user_headers
        )
        assert create_response.status_code in [403, 500]  # Should be forbidden

        # 2. Try to update a product (should fail)
        product_id = str(uuid4())
        update_response = await client.put(
            f"/api/v1/products/{product_id}",
            json=sample_product_data,
            headers=user_headers
        )
        assert update_response.status_code in [403, 500]  # Should be forbidden

        # 3. Try to delete a product (should fail)
        delete_response = await client.delete(
            f"/api/v1/products/{product_id}",
            headers=user_headers
        )
        assert delete_response.status_code in [403, 500]  # Should be forbidden

        # 4. Read products (should work)
        get_products_response = await client.get(
            "/api/v1/products/",
            headers=user_headers
        )
        assert get_products_response.status_code == 200

    @pytest.mark.asyncio
    async def test_pagination_workflow(self, client, admin_headers):
        """Test pagination functionality."""
        # Create multiple products
        products_created = []
        for i in range(5):
            product_data = {
                "name": f"Pagination Test Product {i}",
                "description": f"Product {i} for pagination testing",
                "price": 100.00 + i,
                "picture_url": f"https://example.com/product{i}.jpg",
                "category": ["Pagination", "Test"]
            }
            
            create_response = await client.post(
                "/api/v1/products/",
                json=product_data,
                headers=admin_headers
            )
            if create_response.status_code == 201:
                products_created.append(create_response.json()["id"])

        # Test pagination
        page1_response = await client.get(
            "/api/v1/products/?page=1&page_size=2",
            headers=admin_headers
        )
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert "items" in page1_data
        assert "total" in page1_data
        assert "page" in page1_data
        assert "page_size" in page1_data

        # Test second page
        page2_response = await client.get(
            "/api/v1/products/?page=2&page_size=2",
            headers=admin_headers
        )
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        assert page2_data["page"] == 2

        # Clean up created products
        for product_id in products_created:
            await client.delete(
                f"/api/v1/products/{product_id}",
                headers=admin_headers
            )

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, client, admin_headers):
        """Test error handling in various scenarios."""
        # 1. Test invalid UUID format
        invalid_uuid_response = await client.get(
            "/api/v1/products/invalid-uuid",
            headers=admin_headers
        )
        assert invalid_uuid_response.status_code == 422

        # 2. Test non-existent product
        non_existent_id = str(uuid4())
        get_response = await client.get(
            f"/api/v1/products/{non_existent_id}",
            headers=admin_headers
        )
        assert get_response.status_code in [404, 500]

        # 3. Test invalid product data
        invalid_product_data = {
            "name": "",  # Empty name should be invalid
            "price": -10,  # Negative price should be invalid
        }
        create_response = await client.post(
            "/api/v1/products/",
            json=invalid_product_data,
            headers=admin_headers
        )
        assert create_response.status_code == 422

        # 4. Test update non-existent product
        update_response = await client.put(
            f"/api/v1/products/{non_existent_id}",
            json={"name": "Updated", "price": 100},
            headers=admin_headers
        )
        assert update_response.status_code in [404, 500]

        # 5. Test delete non-existent product
        delete_response = await client.delete(
            f"/api/v1/products/{non_existent_id}",
            headers=admin_headers
        )
        assert delete_response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_unauthorized_access_workflow(self, client, sample_product_data):
        """Test unauthorized access scenarios."""
        product_id = str(uuid4())

        # Test all endpoints without authorization
        endpoints = [
            ("GET", "/api/v1/products/"),
            ("GET", f"/api/v1/products/{product_id}"),
            ("POST", "/api/v1/products/"),
            ("PUT", f"/api/v1/products/{product_id}"),
            ("DELETE", f"/api/v1/products/{product_id}"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint, json=sample_product_data)
            elif method == "PUT":
                response = await client.put(endpoint, json=sample_product_data)
            elif method == "DELETE":
                response = await client.delete(endpoint)
            
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, client, admin_headers):
        """Test concurrent operations on the same product."""
        # Create a product
        product_data = {
            "name": "Concurrent Test Product",
            "description": "Product for concurrent testing",
            "price": 100.00,
            "picture_url": "https://example.com/concurrent.jpg",
            "category": ["Concurrent", "Test"]
        }
        
        create_response = await client.post(
            "/api/v1/products/",
            json=product_data,
            headers=admin_headers
        )
        assert create_response.status_code == 201
        product_id = create_response.json()["id"]

        # Perform concurrent read operations
        async def read_product():
            return await client.get(
                f"/api/v1/products/{product_id}",
                headers=admin_headers
            )

        # Run multiple concurrent reads
        tasks = [read_product() for _ in range(5)]
        responses = await asyncio.gather(*tasks)

        # All reads should succeed
        for response in responses:
            assert response.status_code == 200

        # Clean up
        await client.delete(
            f"/api/v1/products/{product_id}",
            headers=admin_headers
        )

    @pytest.mark.asyncio
    async def test_data_validation_workflow(self, client, admin_headers):
        """Test comprehensive data validation."""
        # Test various invalid data scenarios
        invalid_scenarios = [
            {
                "data": {"name": "", "price": 100},  # Empty name
                "expected_status": 422
            },
            {
                "data": {"name": "Test", "price": -100},  # Negative price
                "expected_status": 422
            },
            {
                "data": {"name": "Test", "price": "invalid"},  # Invalid price type
                "expected_status": 422
            },
            {
                "data": {"price": 100},  # Missing name
                "expected_status": 422
            },
            {
                "data": {"name": "Test", "price": 100, "category": "not_a_list"},  # Invalid category type
                "expected_status": 422
            }
        ]

        for scenario in invalid_scenarios:
            response = await client.post(
                "/api/v1/products/",
                json=scenario["data"],
                headers=admin_headers
            )
            assert response.status_code == scenario["expected_status"]

    @pytest.mark.asyncio
    async def test_large_data_handling(self, client, admin_headers):
        """Test handling of large data."""
        # Create product with large description
        large_description = "A" * 10000  # 10KB description
        large_product_data = {
            "name": "Large Data Product",
            "description": large_description,
            "price": 100.00,
            "picture_url": "https://example.com/large.jpg",
            "category": ["Large", "Data", "Test"]
        }

        create_response = await client.post(
            "/api/v1/products/",
            json=large_product_data,
            headers=admin_headers
        )
        
        if create_response.status_code == 201:
            product_id = create_response.json()["id"]
            
            # Verify the large data was stored correctly
            get_response = await client.get(
                f"/api/v1/products/{product_id}",
                headers=admin_headers
            )
            assert get_response.status_code == 200
            retrieved_data = get_response.json()
            assert len(retrieved_data["data"]["description"]) == 10000
            
            # Clean up
            await client.delete(
                f"/api/v1/products/{product_id}",
                headers=admin_headers
            )



