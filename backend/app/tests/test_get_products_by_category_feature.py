"""Tests for get products by category feature."""

from typing import Any, cast
from uuid import uuid4

import pytest
from app.modules.catalog.application.features.products.queries.get_products_by_category.get_products_by_category_query import (
    GetProductsByCategoryQuery, GetProductsByCategoryResult)
from app.modules.catalog.application.public_interface.dto.product import \
    ProductDto
from pydantic import ValidationError


def _product_dto(**kwargs: object) -> ProductDto:
    """Build ProductDto with required test defaults."""
    defaults: dict[str, object] = {
        "sku": "TEST-SKU",
        "version": 1,
        "created_at": "2020-01-01T00:00:00Z",
        "name": "Test",
        "description": "D",
        "price": 1.0,
        "category": [],
        "image_file": None,
    }
    defaults.update(kwargs)
    if "id" not in defaults:
        defaults["id"] = uuid4()
    return ProductDto(**cast(Any, defaults))


class TestGetProductsByCategoryQuery:
    """Test GetProductsByCategoryQuery."""

    def test_query_creation(self) -> None:
        """Test creating a GetProductsByCategoryQuery."""
        query = GetProductsByCategoryQuery(category="Electronics")

        assert query.category == "Electronics"
        assert query.page == 1
        assert query.page_size == 10

    def test_query_creation_with_pagination(self) -> None:
        """Test creating a query with custom pagination."""
        query = GetProductsByCategoryQuery(category="Electronics", page=2, page_size=20)

        assert query.category == "Electronics"
        assert query.page == 2
        assert query.page_size == 20

    def test_query_validation_missing_category(self) -> None:
        """Test query validation with missing category."""
        with pytest.raises(ValidationError):
            GetProductsByCategoryQuery(**cast(Any, {}))

    def test_query_validation_empty_category(self) -> None:
        """Test query validation with empty category."""
        with pytest.raises(ValidationError):
            GetProductsByCategoryQuery(category="")

    def test_query_validation_invalid_page(self) -> None:
        """Test query validation with invalid page number."""
        with pytest.raises(ValidationError):
            GetProductsByCategoryQuery(category="Electronics", page=0)

    def test_query_validation_invalid_page_size(self) -> None:
        """Test query validation with invalid page size."""
        with pytest.raises(ValidationError):
            GetProductsByCategoryQuery(category="Electronics", page_size=0)

        with pytest.raises(ValidationError):
            GetProductsByCategoryQuery(category="Electronics", page_size=101)

    def test_query_serialization(self) -> None:
        """Test query serialization."""
        query = GetProductsByCategoryQuery(category="Electronics", page=2, page_size=20)

        data = query.model_dump()
        assert data["category"] == "Electronics"
        assert data["page"] == 2
        assert data["page_size"] == 20

    def test_query_deserialization(self) -> None:
        """Test query deserialization."""
        data = {
            "category": "Electronics",
            "page": 2,
            "page_size": 20,
        }

        query = GetProductsByCategoryQuery(**cast(dict[str, Any], data))
        assert query.category == "Electronics"
        assert query.page == 2
        assert query.page_size == 20

    def test_query_round_trip(self) -> None:
        """Test query serialization round trip."""
        original_query = GetProductsByCategoryQuery(
            category="Electronics", page=2, page_size=20
        )

        # Serialize
        data = original_query.model_dump()

        # Deserialize
        reconstructed_query = GetProductsByCategoryQuery(**data)

        assert reconstructed_query.category == original_query.category
        assert reconstructed_query.page == original_query.page
        assert reconstructed_query.page_size == original_query.page_size

    def test_query_with_category_id(self) -> None:
        """Test query with optional category_id."""
        category_id = uuid4()
        query = GetProductsByCategoryQuery(
            category="Electronics", category_id=category_id
        )

        assert query.category == "Electronics"
        assert query.category_id == category_id


class TestGetProductsByCategoryResult:
    """Test GetProductsByCategoryResult."""

    def test_result_creation(self) -> None:
        """Test creating a GetProductsByCategoryResult."""
        products = [
            _product_dto(
                id=uuid4(),
                name="Product 1",
                description="Description 1",
                price=99.99,
                category=["Electronics"],
            ),
            _product_dto(
                id=uuid4(),
                name="Product 2",
                description="Description 2",
                price=149.99,
                category=["Electronics"],
            ),
        ]

        result = GetProductsByCategoryResult(
            items=products, total=2, page=1, size=10, pages=1, category="Electronics"
        )

        assert len(result.items) == 2
        assert result.total == 2
        assert result.page == 1
        assert result.size == 10
        assert result.pages == 1
        assert result.category == "Electronics"

    def test_result_empty_list(self) -> None:
        """Test result with empty product list."""
        result = GetProductsByCategoryResult(
            items=[], total=0, page=1, size=10, pages=0, category="Electronics"
        )

        assert len(result.items) == 0
        assert result.total == 0
        assert result.pages == 0
        assert result.category == "Electronics"

    def test_result_pagination(self) -> None:
        """Test result with pagination."""
        products = [
            _product_dto(
                id=uuid4(),
                name=f"Product {i}",
                description=f"Description {i}",
                price=99.99,
                category=["Electronics"],
            )
            for i in range(1, 11)
        ]

        result = GetProductsByCategoryResult(
            items=products,
            total=25,
            page=2,
            size=10,
            pages=3,
            category="Electronics",
        )

        assert len(result.items) == 10
        assert result.total == 25
        assert result.page == 2
        assert result.size == 10
        assert result.pages == 3

    def test_result_serialization(self) -> None:
        """Test result serialization."""
        products = [
            _product_dto(
                id=uuid4(),
                name="Product 1",
                description="Description 1",
                price=99.99,
                category=["Electronics"],
            )
        ]

        result = GetProductsByCategoryResult(
            items=products, total=1, page=1, size=10, pages=1, category="Electronics"
        )

        data = result.model_dump()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["category"] == "Electronics"

    def test_result_validation_missing_category(self) -> None:
        """Test result validation with missing category."""
        products = [
            _product_dto(
                id=uuid4(),
                name="Product 1",
                description="Description 1",
                price=99.99,
                category=["Electronics"],
            )
        ]

        incomplete: dict[str, Any] = {
            "items": products,
            "total": 1,
            "page": 1,
            "size": 10,
            "pages": 1,
        }
        with pytest.raises(ValidationError):
            GetProductsByCategoryResult(**incomplete)


class TestGetProductsByCategoryFeatureIntegration:
    """Integration tests for get products by category feature."""

    def test_query_and_result_workflow(self) -> None:
        """Test complete workflow from query to result."""
        # Create a query
        query = GetProductsByCategoryQuery(category="Electronics", page=1, page_size=10)

        # Create products
        products = [
            _product_dto(
                id=uuid4(),
                name="Product 1",
                description="Description 1",
                price=99.99,
                category=["Electronics"],
            ),
            _product_dto(
                id=uuid4(),
                name="Product 2",
                description="Description 2",
                price=149.99,
                category=["Electronics"],
            ),
        ]

        # Create a result
        result = GetProductsByCategoryResult(
            items=products, total=2, page=1, size=10, pages=1, category="Electronics"
        )

        # Verify the workflow
        assert query.category == result.category
        assert len(result.items) == 2
        assert result.page == query.page
        assert result.size == query.page_size

    def test_query_and_result_empty_category(self) -> None:
        """Test workflow when no products found for category."""
        # Create a query
        query = GetProductsByCategoryQuery(category="NonExistent", page=1, page_size=10)

        # Create a result indicating no products
        result = GetProductsByCategoryResult(
            items=[], total=0, page=1, size=10, pages=0, category="NonExistent"
        )

        # Verify the workflow
        assert query.category == result.category
        assert len(result.items) == 0
        assert result.total == 0

    def test_multiple_queries_and_results(self) -> None:
        """Test multiple queries and results for different categories."""
        categories = ["Electronics", "Gadgets", "Books"]
        queries = [
            GetProductsByCategoryQuery(category=cat, page=1, page_size=10)
            for cat in categories
        ]
        results = [
            GetProductsByCategoryResult(
                items=[],
                total=0,
                page=1,
                size=10,
                pages=0,
                category=cat,
            )
            for cat in categories
        ]

        # Verify all queries and results are valid
        for query, result in zip(queries, results, strict=False):
            assert query.category == result.category
            assert len(result.items) == 0

    def test_query_result_consistency(self) -> None:
        """Test consistency between query and result."""
        query = GetProductsByCategoryQuery(category="Electronics", page=2, page_size=20)

        products = [
            _product_dto(
                id=uuid4(),
                name=f"Product {i}",
                description=f"Description {i}",
                price=99.99,
                category=["Electronics"],
            )
            for i in range(1, 21)
        ]

        result = GetProductsByCategoryResult(
            items=products,
            total=50,
            page=2,
            size=20,
            pages=3,
            category="Electronics",
        )

        # Verify consistency
        assert query.category == result.category
        assert query.page == result.page
        assert query.page_size == result.size
        assert len(result.items) <= result.size
