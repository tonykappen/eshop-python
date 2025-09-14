"""Tests for Catalog contracts and DTOs."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.modules.catalog.contracts.products.dtos import ProductDto
from app.modules.catalog.contracts.products.features.get_product_by_id import (
    GetProductByIdQuery,
    GetProductByIdResult,
)


class TestProductDto:
    """Test ProductDto validation and serialization."""

    def test_product_dto_valid_data(self):
        """Test ProductDto with valid data."""
        product_id = uuid4()
        dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="A test product description",
            price=Decimal("99.99"),
            picture_url="https://example.com/image.jpg",
            category=["Electronics", "Gadgets"]
        )
        
        assert dto.id == product_id
        assert dto.name == "Test Product"
        assert dto.description == "A test product description"
        assert dto.price == Decimal("99.99")
        assert dto.picture_url == "https://example.com/image.jpg"
        assert dto.category == ["Electronics", "Gadgets"]

    def test_product_dto_minimal_data(self):
        """Test ProductDto with minimal required data."""
        product_id = uuid4()
        dto = ProductDto(
            id=product_id,
            name="Minimal Product",
            description="Minimal description",
            price=Decimal("0.01"),
            picture_url="image.jpg",
            category=["General"]
        )
        
        assert dto.id == product_id
        assert dto.name == "Minimal Product"
        assert dto.price == Decimal("0.01")

    def test_product_dto_serialization(self):
        """Test ProductDto serialization to dict."""
        product_id = uuid4()
        dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="A test product description",
            price=Decimal("99.99"),
            picture_url="https://example.com/image.jpg",
            category=["Electronics", "Gadgets"]
        )
        
        data = dto.dict()
        
        assert data["id"] == product_id  # UUID is kept as UUID object in dict()
        assert data["name"] == "Test Product"
        assert data["description"] == "A test product description"
        assert data["price"] == Decimal("99.99")  # Decimal is kept as Decimal in dict()
        assert data["picture_url"] == "https://example.com/image.jpg"
        assert data["category"] == ["Electronics", "Gadgets"]

    def test_product_dto_deserialization(self):
        """Test ProductDto deserialization from dict."""
        product_id = uuid4()
        data = {
            "id": str(product_id),
            "name": "Test Product",
            "description": "A test product description",
            "price": "99.99",
            "picture_url": "https://example.com/image.jpg",
            "category": ["Electronics", "Gadgets"]
        }
        
        dto = ProductDto(**data)
        
        assert dto.id == product_id
        assert dto.name == "Test Product"
        assert dto.price == Decimal("99.99")

    def test_product_dto_validation_errors(self):
        """Test ProductDto validation with invalid data."""
        product_id = uuid4()
        
        # Test missing required fields
        with pytest.raises(ValidationError) as exc_info:
            ProductDto(
                id=product_id,
                # Missing name
                description="Test description",
                price=Decimal("99.99"),
                picture_url="image.jpg",
                category=["Electronics"]
            )
        
        assert "name" in str(exc_info.value)
        
        # Test invalid price
        with pytest.raises(ValidationError) as exc_info:
            ProductDto(
                id=product_id,
                name="Test Product",
                description="Test description",
                price="invalid_price",  # Invalid price
                picture_url="image.jpg",
                category=["Electronics"]
            )
        
        assert "price" in str(exc_info.value)

    def test_product_dto_empty_category(self):
        """Test ProductDto with empty category list."""
        product_id = uuid4()
        dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            picture_url="image.jpg",
            category=[]  # Empty category list
        )
        
        assert dto.category == []

    def test_product_dto_large_decimal_price(self):
        """Test ProductDto with large decimal price."""
        product_id = uuid4()
        dto = ProductDto(
            id=product_id,
            name="Expensive Product",
            description="Very expensive product",
            price=Decimal("999999.99"),
            picture_url="image.jpg",
            category=["Luxury"]
        )
        
        assert dto.price == Decimal("999999.99")

    def test_product_dto_unicode_name(self):
        """Test ProductDto with unicode characters in name."""
        product_id = uuid4()
        dto = ProductDto(
            id=product_id,
            name="Tëst Pröduct 产品测试",
            description="Unicode description",
            price=Decimal("99.99"),
            picture_url="image.jpg",
            category=["Unicode"]
        )
        
        assert dto.name == "Tëst Pröduct 产品测试"

    def test_product_dto_long_description(self):
        """Test ProductDto with long description."""
        product_id = uuid4()
        long_description = "A" * 1000  # 1000 character description
        dto = ProductDto(
            id=product_id,
            name="Test Product",
            description=long_description,
            price=Decimal("99.99"),
            picture_url="image.jpg",
            category=["Test"]
        )
        
        assert dto.description == long_description
        assert len(dto.description) == 1000


class TestGetProductByIdQuery:
    """Test GetProductByIdQuery validation and serialization."""

    def test_get_product_by_id_query_valid_id(self):
        """Test GetProductByIdQuery with valid UUID."""
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        assert query.id == product_id

    def test_get_product_by_id_query_string_id(self):
        """Test GetProductByIdQuery with string UUID."""
        product_id = uuid4()
        query = GetProductByIdQuery(id=str(product_id))
        
        assert query.id == product_id

    def test_get_product_by_id_query_serialization(self):
        """Test GetProductByIdQuery serialization."""
        product_id = uuid4()
        query = GetProductByIdQuery(id=product_id)
        
        data = query.dict()
        
        assert data["id"] == product_id  # UUID is kept as UUID object in dict()

    def test_get_product_by_id_query_deserialization(self):
        """Test GetProductByIdQuery deserialization."""
        product_id = uuid4()
        data = {"id": str(product_id)}
        
        query = GetProductByIdQuery(**data)
        
        assert query.id == product_id

    def test_get_product_by_id_query_validation_error(self):
        """Test GetProductByIdQuery with invalid UUID."""
        with pytest.raises(ValidationError) as exc_info:
            GetProductByIdQuery(id="invalid-uuid")
        
        assert "id" in str(exc_info.value)

    def test_get_product_by_id_query_missing_id(self):
        """Test GetProductByIdQuery with missing ID."""
        with pytest.raises(ValidationError) as exc_info:
            GetProductByIdQuery()
        
        assert "id" in str(exc_info.value)


class TestGetProductByIdResult:
    """Test GetProductByIdResult validation and serialization."""

    def test_get_product_by_id_result_with_product(self):
        """Test GetProductByIdResult with product."""
        product_id = uuid4()
        product = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            picture_url="image.jpg",
            category=["Electronics"]
        )
        
        result = GetProductByIdResult(product=product)
        
        assert result.product == product
        assert result.product.id == product_id

    def test_get_product_by_id_result_without_product(self):
        """Test GetProductByIdResult without product (None)."""
        result = GetProductByIdResult(product=None)
        
        assert result.product is None

    def test_get_product_by_id_result_serialization(self):
        """Test GetProductByIdResult serialization."""
        product_id = uuid4()
        product = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            picture_url="image.jpg",
            category=["Electronics"]
        )
        
        result = GetProductByIdResult(product=product)
        data = result.dict()
        
        assert "product" in data
        assert data["product"]["id"] == product_id  # UUID is kept as UUID object in dict()
        assert data["product"]["name"] == "Test Product"

    def test_get_product_by_id_result_serialization_none(self):
        """Test GetProductByIdResult serialization with None product."""
        result = GetProductByIdResult(product=None)
        data = result.dict()
        
        assert data["product"] is None

    def test_get_product_by_id_result_deserialization(self):
        """Test GetProductByIdResult deserialization."""
        product_id = uuid4()
        data = {
            "product": {
                "id": str(product_id),
                "name": "Test Product",
                "description": "Test description",
                "price": "99.99",
                "picture_url": "image.jpg",
                "category": ["Electronics"]
            }
        }
        
        result = GetProductByIdResult(**data)
        
        assert result.product is not None
        assert result.product.id == product_id
        assert result.product.name == "Test Product"

    def test_get_product_by_id_result_deserialization_none(self):
        """Test GetProductByIdResult deserialization with None product."""
        data = {"product": None}
        
        result = GetProductByIdResult(**data)
        
        assert result.product is None


class TestDTOEdgeCases:
    """Test edge cases and boundary conditions for DTOs."""

    def test_product_dto_zero_price_validation_error(self):
        """Test ProductDto with zero price raises validation error."""
        product_id = uuid4()
        
        with pytest.raises(ValidationError) as exc_info:
            ProductDto(
                id=product_id,
                name="Free Product",
                description="Free product",
                price=Decimal("0.00"),  # This should fail validation
                picture_url="image.jpg",
                category=["Free"]
            )
        
        assert "price" in str(exc_info.value)
        assert "greater than 0" in str(exc_info.value)

    def test_product_dto_very_small_price(self):
        """Test ProductDto with very small price."""
        product_id = uuid4()
        dto = ProductDto(
            id=product_id,
            name="Cheap Product",
            description="Very cheap product",
            price=Decimal("0.01"),
            picture_url="image.jpg",
            category=["Cheap"]
        )
        
        assert dto.price == Decimal("0.01")

    def test_product_dto_special_characters(self):
        """Test ProductDto with special characters."""
        product_id = uuid4()
        dto = ProductDto(
            id=product_id,
            name="Product with Special Ch@rs!",
            description="Description with émojis 🚀 and spëcial chars",
            price=Decimal("99.99"),
            picture_url="https://example.com/image-with-special-chars.jpg",
            category=["Special", "Unicode", "Test"]
        )
        
        assert dto.name == "Product with Special Ch@rs!"
        assert "émojis" in dto.description
        assert "🚀" in dto.description

    def test_product_dto_long_url(self):
        """Test ProductDto with very long URL."""
        product_id = uuid4()
        long_url = "https://example.com/" + "a" * 1000 + ".jpg"
        dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            picture_url=long_url,
            category=["Test"]
        )
        
        assert dto.picture_url == long_url
        assert len(dto.picture_url) > 1000

    def test_product_dto_many_categories(self):
        """Test ProductDto with many categories."""
        product_id = uuid4()
        many_categories = [f"Category{i}" for i in range(100)]
        dto = ProductDto(
            id=product_id,
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            picture_url="image.jpg",
            category=many_categories
        )
        
        assert len(dto.category) == 100
        assert dto.category[0] == "Category0"
        assert dto.category[-1] == "Category99"
