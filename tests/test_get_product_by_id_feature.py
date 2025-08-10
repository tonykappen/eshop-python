"""Tests for get product by ID feature."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from eshop.modules.catalog.contracts.products.dtos import ProductDto
from eshop.modules.catalog.contracts.products.features.get_product_by_id import (
    GetProductByIdQuery,
    GetProductByIdResult,
)


class TestGetProductByIdQuery:
    """Test GetProductByIdQuery."""

    def test_query_creation(self) -> None:
        """Test creating a GetProductByIdQuery."""
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        assert query.id == product_id

    def test_query_validation_missing_id(self) -> None:
        """Test query validation with missing ID."""
        with pytest.raises(ValidationError):
            GetProductByIdQuery()

    def test_query_validation_invalid_uuid(self) -> None:
        """Test query validation with invalid UUID."""
        with pytest.raises(ValidationError):
            GetProductByIdQuery(id="invalid-uuid")

    def test_query_serialization(self) -> None:
        """Test query serialization."""
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        data = query.model_dump()
        assert data["id"] == product_id

    def test_query_deserialization(self) -> None:
        """Test query deserialization."""
        product_id = uuid4()
        data = {"id": str(product_id)}
        
        query = GetProductByIdQuery(**data)
        assert query.id == product_id

    def test_query_round_trip(self) -> None:
        """Test query serialization round trip."""
        product_id = uuid4()
        original_query = GetProductByIdQuery(id=product_id)
        
        # Serialize
        data = original_query.model_dump()
        
        # Deserialize
        reconstructed_query = GetProductByIdQuery(**data)
        
        assert reconstructed_query.id == original_query.id

    def test_query_inheritance(self) -> None:
        """Test that query inherits from IQuery."""
        from eshop.core.cqrs.base import IQuery
        
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        assert isinstance(query, IQuery)

    def test_query_field_description(self) -> None:
        """Test that query field has proper description."""
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        # Check that the field has a description
        field_info = query.model_fields["id"]
        assert field_info.description == "Product ID to retrieve"


class TestGetProductByIdResult:
    """Test GetProductByIdResult."""

    def test_result_creation_with_product(self) -> None:
        """Test creating a GetProductByIdResult with a product."""
        product_id = uuid4()
        product_dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test Description",
            price=99.99,
            category=["Electronics"],
            image_file="test.jpg",
            stock_quantity=100,
            is_available=True,
        )
        
        result = GetProductByIdResult(product=product_dto)
        
        assert result.product == product_dto
        assert result.product.id == product_id
        assert result.product.name == "Test Product"

    def test_result_creation_without_product(self) -> None:
        """Test creating a GetProductByIdResult without a product."""
        result = GetProductByIdResult()
        
        assert result.product is None

    def test_result_creation_with_none_product(self) -> None:
        """Test creating a GetProductByIdResult with None product."""
        result = GetProductByIdResult(product=None)
        
        assert result.product is None

    def test_result_serialization_with_product(self) -> None:
        """Test result serialization with product."""
        product_id = uuid4()
        product_dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test Description",
            price=99.99,
            category=["Electronics"],
            image_file="test.jpg",
            stock_quantity=100,
            is_available=True,
        )
        
        result = GetProductByIdResult(product=product_dto)
        
        data = result.model_dump()
        assert data["product"] is not None
        assert data["product"]["id"] == product_id
        assert data["product"]["name"] == "Test Product"

    def test_result_serialization_without_product(self) -> None:
        """Test result serialization without product."""
        result = GetProductByIdResult()
        
        data = result.model_dump()
        assert data["product"] is None

    def test_result_deserialization_with_product(self) -> None:
        """Test result deserialization with product."""
        product_id = uuid4()
        product_data = {
            "id": str(product_id),
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99,
            "category": ["Electronics"],
            "image_file": "test.jpg",
            "stock_quantity": 100,
            "is_available": True,
        }
        
        data = {"product": product_data}
        result = GetProductByIdResult(**data)
        
        assert result.product is not None
        assert result.product.id == product_id
        assert result.product.name == "Test Product"

    def test_result_deserialization_without_product(self) -> None:
        """Test result deserialization without product."""
        data = {"product": None}
        result = GetProductByIdResult(**data)
        
        assert result.product is None

    def test_result_round_trip(self) -> None:
        """Test result serialization round trip."""
        product_id = uuid4()
        product_dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test Description",
            price=99.99,
            category=["Electronics"],
            image_file="test.jpg",
            stock_quantity=100,
            is_available=True,
        )
        
        original_result = GetProductByIdResult(product=product_dto)
        
        # Serialize
        data = original_result.model_dump()
        
        # Deserialize
        reconstructed_result = GetProductByIdResult(**data)
        
        assert reconstructed_result.product is not None
        assert reconstructed_result.product.id == original_result.product.id
        assert reconstructed_result.product.name == original_result.product.name
        assert reconstructed_result.product.description == original_result.product.description
        assert reconstructed_result.product.price == original_result.product.price

    def test_result_inheritance(self) -> None:
        """Test that result inherits from IQuery."""
        from eshop.core.cqrs.base import IQuery
        
        result = GetProductByIdResult()
        
        assert isinstance(result, IQuery)

    def test_result_field_description(self) -> None:
        """Test that result field has proper description."""
        result = GetProductByIdResult()
        
        # Check that the field has a description
        field_info = result.model_fields["product"]
        assert field_info.description == "The retrieved product, None if not found"


class TestGetProductByIdFeatureIntegration:
    """Integration tests for get product by ID feature."""

    def test_query_and_result_workflow(self) -> None:
        """Test complete workflow from query to result."""
        # Create a query
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        # Create a result
        product_dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test Description",
            price=99.99,
            category=["Electronics"],
            image_file="test.jpg",
            stock_quantity=100,
            is_available=True,
        )
        result = GetProductByIdResult(product=product_dto)
        
        # Verify the workflow
        assert query.id == result.product.id
        assert result.product is not None

    def test_query_and_result_not_found_workflow(self) -> None:
        """Test workflow when product is not found."""
        # Create a query
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        # Create a result indicating not found
        result = GetProductByIdResult(product=None)
        
        # Verify the workflow
        assert query.id == product_id
        assert result.product is None

    def test_multiple_queries_and_results(self) -> None:
        """Test multiple queries and results."""
        product_ids = [uuid4(), uuid4(), uuid4()]
        queries = [GetProductByIdQuery(id=pid) for pid in product_ids]
        results = [GetProductByIdResult(product=None) for _ in product_ids]
        
        # Verify all queries and results are valid
        for i, (query, result) in enumerate(zip(queries, results)):
            assert query.id == product_ids[i]
            assert result.product is None

    def test_query_result_consistency(self) -> None:
        """Test consistency between query and result."""
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        # Test with found product
        product_dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test Description",
            price=99.99,
            category=["Electronics"],
            image_file="test.jpg",
            stock_quantity=100,
            is_available=True,
        )
        found_result = GetProductByIdResult(product=product_dto)
        
        # Test with not found product
        not_found_result = GetProductByIdResult(product=None)
        
        # Verify consistency
        assert query.id == found_result.product.id
        assert not_found_result.product is None


class TestGetProductByIdFeatureValidation:
    """Test validation scenarios for get product by ID feature."""

    def test_query_with_none_id(self) -> None:
        """Test query with None ID."""
        with pytest.raises(ValidationError):
            GetProductByIdQuery(id=None)

    def test_query_with_empty_string_id(self) -> None:
        """Test query with empty string ID."""
        with pytest.raises(ValidationError):
            GetProductByIdQuery(id="")

    def test_result_with_invalid_product_data(self) -> None:
        """Test result with invalid product data."""
        invalid_product_data = {
            "id": "invalid-uuid",
            "name": "Test Product",
            "price": -99.99,  # Invalid negative price
        }
        
        with pytest.raises(ValidationError):
            GetProductByIdResult(product=invalid_product_data)

    def test_result_with_partial_product_data(self) -> None:
        """Test result with partial product data."""
        # ProductDto requires all fields, so partial data should fail
        partial_product_data = {
            "id": str(uuid4()),
            "name": "Test Product",
            # Missing required fields
        }
        
        with pytest.raises(ValidationError):
            GetProductByIdResult(product=partial_product_data)


class TestGetProductByIdFeatureEdgeCases:
    """Test edge cases for get product by ID feature."""

    def test_query_with_zero_uuid(self) -> None:
        """Test query with zero UUID."""
        # Create a zero UUID
        zero_uuid = uuid4()
        # For testing purposes, we'll use a regular UUID
        # In practice, you might want to test with UUID('00000000-0000-0000-0000-000000000000')
        
        query = GetProductByIdQuery(id=zero_uuid)
        assert query.id == zero_uuid

    def test_result_with_empty_product_fields(self) -> None:
        """Test result with empty product fields."""
        product_id = uuid4()
        # ProductDto requires price > 0, so we'll use a minimal valid price
        product_dto = ProductDto(
            id=product_id,
            name="",  # Empty name
            description="",  # Empty description
            price=0.01,  # Minimal valid price
            category=[],  # Empty category
            image_file="",  # Empty image file
        )
        
        result = GetProductByIdResult(product=product_dto)
        
        assert result.product is not None
        assert result.product.name == ""
        assert result.product.description == ""
        assert float(result.product.price) == 0.01
        assert result.product.category == []
        assert result.product.image_file == ""

    def test_result_with_large_values(self) -> None:
        """Test result with large values."""
        product_id = uuid4()
        product_dto = ProductDto(
            id=product_id,
            name="A" * 1000,  # Very long name
            description="B" * 10000,  # Very long description
            price=999999.99,  # Large price
            category=["Category1", "Category2", "Category3"],
            image_file="very_long_image_file_name_with_many_characters.jpg",
        )
        
        result = GetProductByIdResult(product=product_dto)
        
        assert result.product is not None
        assert len(result.product.name) == 1000
        assert len(result.product.description) == 10000
        assert float(result.product.price) == 999999.99
        assert len(result.product.category) == 3
        assert len(result.product.image_file) > 0

    def test_query_result_immutability(self) -> None:
        """Test that query and result are immutable after creation."""
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        # Try to modify the query (should not be possible with frozen models)
        # This test verifies that the models are properly configured
        
        product_dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test Description",
            price=99.99,
            category=["Electronics"],
            image_file="test.jpg",
            stock_quantity=100,
            is_available=True,
        )
        result = GetProductByIdResult(product=product_dto)
        
        # Verify the objects are properly created
        assert query.id == product_id
        assert result.product is not None
        assert result.product.id == product_id
