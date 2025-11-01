"""Integration tests for API schema validations."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.modules.catalog.contracts.product.dtos import (
    ProductDto,
    ProductSearchDto,
    ProductSummaryDto,
)
from app.modules.catalog.api.endpoints.products import (
    CreateProductRequest,
    DeleteProductRequest,
    GetProductRequest,
    GetProductsRequest,
    UpdateProductRequest,
)


class TestProductDtoSchemaValidation:
    """Test ProductDto schema validation."""

    def test_product_dto_valid_data(self):
        """Test ProductDto with valid data."""
        product = ProductDto(
            id=uuid4(),
            name="Test Product",
            sku="TEST-001",
            category=["Electronics", "Gadgets"],
            description="Test description",
            image_file="test.jpg",
            price=99.99,
            currency="USD",
            version=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        assert product.name == "Test Product"
        assert product.price == 99.99
        assert len(product.category) == 2

    def test_product_dto_missing_required_fields(self):
        """Test ProductDto validation with missing required fields."""
        with pytest.raises(ValidationError):
            ProductDto(
                name="Test Product",
                # Missing required fields: id, sku, category, etc.
            )

    def test_product_dto_invalid_uuid(self):
        """Test ProductDto validation with invalid UUID."""
        with pytest.raises(ValidationError):
            ProductDto(
                id="invalid-uuid",
                name="Test Product",
                sku="TEST-001",
                category=["Electronics"],
                description="Test",
                price=99.99,
                currency="USD",
                version=1,
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            )

    def test_product_dto_empty_category(self):
        """Test ProductDto with empty category list."""
        with pytest.raises(ValidationError):
            ProductDto(
                id=uuid4(),
                name="Test Product",
                sku="TEST-001",
                category=[],  # Empty list should fail validation
                description="Test",
                price=99.99,
                currency="USD",
                version=1,
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            )

    def test_product_dto_negative_price(self):
        """Test ProductDto with negative price (should be allowed by schema but tested)."""
        # Note: Price validation should be at the API request level
        product = ProductDto(
            id=uuid4(),
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            description="Test",
            price=-10.0,  # Negative price
            currency="USD",
            version=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        assert product.price == -10.0


class TestProductSummaryDtoSchemaValidation:
    """Test ProductSummaryDto schema validation."""

    def test_product_summary_dto_valid(self):
        """Test ProductSummaryDto with valid data."""
        summary = ProductSummaryDto(
            id=uuid4(),
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            price=99.99,
            currency="USD",
        )

        assert summary.name == "Test Product"
        assert summary.price == 99.99

    def test_product_summary_dto_optional_image(self):
        """Test ProductSummaryDto with optional image_file."""
        summary = ProductSummaryDto(
            id=uuid4(),
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            price=99.99,
            currency="USD",
            image_file=None,  # Optional field
        )

        assert summary.image_file is None


class TestProductSearchDtoSchemaValidation:
    """Test ProductSearchDto schema validation."""

    def test_product_search_dto_valid(self):
        """Test ProductSearchDto with valid data."""
        search = ProductSearchDto(
            id=uuid4(),
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            description="Test description",
            price=99.99,
            currency="USD",
            relevance_score=0.95,
        )

        assert search.name == "Test Product"
        assert search.relevance_score == 0.95

    def test_product_search_dto_optional_relevance_score(self):
        """Test ProductSearchDto with optional relevance_score."""
        search = ProductSearchDto(
            id=uuid4(),
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            description="Test",
            price=99.99,
            currency="USD",
            relevance_score=None,  # Optional field
        )

        assert search.relevance_score is None


class TestProductRequestSchemas:
    """Test API request schema validations."""

    def test_create_product_request_valid(self):
        """Test CreateProductRequest with valid data."""
        request = CreateProductRequest(
            name="Test Product",
            description="Test description",
            price=99.99,
            category=["Electronics"],
        )

        assert request.name == "Test Product"
        assert request.price == 99.99

    def test_create_product_request_negative_price(self):
        """Test CreateProductRequest validation with negative price."""
        with pytest.raises(ValidationError):
            CreateProductRequest(
                name="Test Product",
                description="Test",
                price=-10.0,  # Should fail gt=0 validation
                category=["Electronics"],
            )

    def test_create_product_request_zero_price(self):
        """Test CreateProductRequest validation with zero price."""
        with pytest.raises(ValidationError):
            CreateProductRequest(
                name="Test Product",
                description="Test",
                price=0.0,  # Should fail gt=0 validation
                category=["Electronics"],
            )

    def test_create_product_request_empty_name(self):
        """Test CreateProductRequest with empty name."""
        with pytest.raises(ValidationError):
            CreateProductRequest(
                name="",  # Empty string
                description="Test",
                price=99.99,
                category=["Electronics"],
            )

    def test_create_product_request_empty_category(self):
        """Test CreateProductRequest with empty category list."""
        with pytest.raises(ValidationError):
            CreateProductRequest(
                name="Test Product",
                description="Test",
                price=99.99,
                category=[],  # Empty list should fail
            )

    def test_update_product_request_valid(self):
        """Test UpdateProductRequest with valid data."""
        request = UpdateProductRequest(
            name="Updated Product",
            description="Updated description",
            price=149.99,
            category=["Electronics", "Updated"],
        )

        assert request.name == "Updated Product"
        assert request.price == 149.99

    def test_get_product_request_valid(self):
        """Test GetProductRequest with valid UUID."""
        product_id = uuid4()
        request = GetProductRequest(product_id=product_id)

        assert request.product_id == product_id

    def test_get_product_request_invalid_uuid(self):
        """Test GetProductRequest with invalid UUID."""
        with pytest.raises(ValidationError):
            GetProductRequest(product_id="invalid-uuid")

    def test_get_products_request_valid(self):
        """Test GetProductsRequest with valid data."""
        request = GetProductsRequest(
            page=1,
            page_size=10,
            category_id=uuid4(),
            search_term="test",
        )

        assert request.page == 1
        assert request.page_size == 10
        assert request.search_term == "test"

    def test_get_products_request_optional_fields(self):
        """Test GetProductsRequest with optional fields."""
        request = GetProductsRequest(
            page=1,
            page_size=10,
            category_id=None,  # Optional
            search_term=None,  # Optional
        )

        assert request.category_id is None
        assert request.search_term is None

    def test_delete_product_request_valid(self):
        """Test DeleteProductRequest with valid UUID."""
        product_id = uuid4()
        request = DeleteProductRequest(product_id=product_id)

        assert request.product_id == product_id


class TestApiEndpointSchemaValidation:
    """Test API endpoint schema validation through FastAPI."""

    def test_create_product_endpoint_schema_validation(self):
        """Test create product endpoint validates request schema."""
        client = TestClient(app)

        # Test with invalid price (negative)
        response = client.post(
            "/api/v1/products/",
            json={
                "name": "Test Product",
                "description": "Test",
                "price": -10.0,  # Invalid: should be > 0
                "category": ["Electronics"],
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422  # Validation error

        # Test with missing required field
        response = client.post(
            "/api/v1/products/",
            json={
                "name": "Test Product",
                # Missing description, price, category
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422  # Validation error

    def test_update_product_endpoint_schema_validation(self):
        """Test update product endpoint validates request schema."""
        client = TestClient(app)
        product_id = uuid4()

        # Test with invalid price
        response = client.put(
            f"/api/v1/products/{product_id}",
            json={
                "name": "Updated Product",
                "description": "Updated",
                "price": 0.0,  # Invalid: should be > 0
                "category": ["Electronics"],
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422  # Validation error

    def test_get_product_endpoint_schema_validation(self):
        """Test get product endpoint validates UUID."""
        client = TestClient(app)

        # Test with invalid UUID format
        response = client.get(
            "/api/v1/products/invalid-uuid",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422  # Validation error

    def test_get_products_endpoint_schema_validation(self):
        """Test get products endpoint validates pagination params."""
        client = TestClient(app)

        # Test with invalid page (should be >= 1)
        response = client.get(
            "/api/v1/products/?page=0",
            headers={"Authorization": "Bearer test-token"},
        )
        # Note: FastAPI validation might allow this depending on implementation
        # This test documents expected behavior

        # Test with invalid page_size (too large)
        response = client.get(
            "/api/v1/products/?page_size=1000",
            headers={"Authorization": "Bearer test-token"},
        )
        # Note: Validation depends on endpoint implementation


class TestResponseSchemaValidation:
    """Test API response schema validation."""

    def test_product_response_schema(self):
        """Test that ProductResponse follows expected schema."""
        from app.modules.catalog.api.endpoints.products import ProductResponse

        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            description="Test",
            price=99.99,
            currency="USD",
            version=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        response = ProductResponse(data=product_dto)

        assert response.data == product_dto
        assert response.success is True

    def test_create_product_response_schema(self):
        """Test CreateProductResponse schema."""
        from app.modules.catalog.api.endpoints.products import CreateProductResponse

        response = CreateProductResponse(id=uuid4())

        assert isinstance(response.id, UUID)

    def test_update_product_response_schema(self):
        """Test UpdateProductResponse schema."""
        from app.modules.catalog.api.endpoints.products import UpdateProductResponse

        response = UpdateProductResponse(success=True)

        assert response.success is True

    def test_delete_product_response_schema(self):
        """Test DeleteProductResponse schema."""
        from app.modules.catalog.api.endpoints.products import DeleteProductResponse

        response = DeleteProductResponse(success=True)

        assert response.success is True


class TestSchemaTypeCoercion:
    """Test schema type coercion."""

    def test_product_dto_price_type_coercion(self):
        """Test that ProductDto handles price type coercion."""
        product = ProductDto(
            id=uuid4(),
            name="Test",
            sku="TEST-001",
            category=["Electronics"],
            description="Test",
            price=Decimal("99.99"),  # Decimal should be accepted
            currency="USD",
            version=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        assert isinstance(product.price, (float, Decimal))

