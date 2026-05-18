"""Comprehensive tests for pagination models."""

from unittest.mock import MagicMock

import pytest
from app.core.pagination.models import (PaginatedResult, PaginationRequest,
                                        PaginationResponse,
                                        create_paginated_response,
                                        create_pagination_params)
from fastapi_pagination import Params


class TestPaginationRequest:
    """Test PaginationRequest functionality."""

    def test_pagination_request_default_values(self) -> None:
        """Test PaginationRequest with default values."""
        request = PaginationRequest()
        assert request.page == 1
        assert request.size == 10

    def test_pagination_request_custom_values(self) -> None:
        """Test PaginationRequest with custom values."""
        request = PaginationRequest(page=5, size=25)
        assert request.page == 5
        assert request.size == 25

    def test_pagination_request_validation_min_page(self) -> None:
        """Test PaginationRequest validation for minimum page."""
        with pytest.raises(
            ValueError, match="Input should be greater than or equal to 1"
        ):
            PaginationRequest(page=0)

    def test_pagination_request_validation_min_size(self) -> None:
        """Test PaginationRequest validation for minimum size."""
        with pytest.raises(
            ValueError, match="Input should be greater than or equal to 1"
        ):
            PaginationRequest(size=0)

    def test_pagination_request_validation_max_size(self) -> None:
        """Test PaginationRequest validation for maximum size."""
        with pytest.raises(
            ValueError, match="Input should be less than or equal to 100"
        ):
            PaginationRequest(size=101)

    def test_pagination_request_to_params(self) -> None:
        """Test conversion to fastapi-pagination Params."""
        request = PaginationRequest(page=3, size=15)
        params = request.to_params()

        assert isinstance(params, Params)
        assert params.page == 3
        assert params.size == 15

    def test_pagination_request_serialization(self) -> None:
        """Test PaginationRequest serialization."""
        request = PaginationRequest(page=2, size=20)
        data = request.model_dump()

        assert data["page"] == 2
        assert data["size"] == 20

    def test_pagination_request_deserialization(self) -> None:
        """Test PaginationRequest deserialization."""
        data = {"page": 4, "size": 30}
        request = PaginationRequest(**data)

        assert request.page == 4
        assert request.size == 30


class TestPaginatedResult:
    """Test PaginatedResult functionality."""

    def test_paginated_result_creation(self) -> None:
        """Test PaginatedResult basic creation."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = PaginatedResult(items=items, total=10, page=1, size=3, pages=4)

        assert result.items == items
        assert result.total == 10
        assert result.page == 1
        assert result.size == 3
        assert result.pages == 4

    def test_paginated_result_from_page(self) -> None:
        """Test PaginatedResult creation from fastapi-pagination Page."""
        items = [{"id": 1}, {"id": 2}]
        # Create a mock Page object
        page = MagicMock()
        page.items = items
        page.total = 5
        page.page = 1
        page.size = 2
        page.pages = 3

        result = PaginatedResult.from_page(page)

        assert result.items == items
        assert result.total == 5
        assert result.page == 1
        assert result.size == 2
        assert result.pages == 3

    def test_paginated_result_from_page_with_none_values(self) -> None:
        """Test PaginatedResult from Page with None values."""
        items = [{"id": 1}]
        # Create a mock Page object with None values
        page = MagicMock()
        page.items = items
        page.total = None
        page.page = None
        page.size = None
        page.pages = None

        result = PaginatedResult.from_page(page)

        assert result.items == items
        assert result.total == 0
        assert result.page == 1
        assert result.size == 10
        assert result.pages == 1

    def test_paginated_result_create_with_calculation(self) -> None:
        """Test PaginatedResult.create with automatic page calculation."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = PaginatedResult.create(items=items, total=25, page=2, size=3)

        assert result.items == items
        assert result.total == 25
        assert result.page == 2
        assert result.size == 3
        assert result.pages == 9  # (25 + 3 - 1) // 3 = 9

    def test_paginated_result_create_exact_pages(self) -> None:
        """Test PaginatedResult.create with exact page division."""
        items = [{"id": 1}, {"id": 2}]
        result = PaginatedResult.create(items=items, total=10, page=1, size=2)

        assert result.pages == 5  # 10 // 2 = 5

    def test_paginated_result_create_empty_items(self) -> None:
        """Test PaginatedResult.create with empty items."""
        result = PaginatedResult.create(items=[], total=0, page=1, size=10)

        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.size == 10
        assert result.pages == 0  # (0 + 10 - 1) // 10 = 0

    def test_paginated_result_serialization(self) -> None:
        """Test PaginatedResult serialization."""
        items = [{"id": 1}, {"id": 2}]
        result = PaginatedResult.create(items, total=5, page=1, size=2)
        data = result.model_dump()

        assert data["items"] == items
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["pages"] == 3

    def test_paginated_result_generic_type_safety(self) -> None:
        """Test PaginatedResult generic type safety."""
        # This should work with any type
        int_items = [1, 2, 3]
        int_result = PaginatedResult[int].create(int_items, total=10, page=1, size=3)
        assert int_result.items == int_items

        str_items = ["a", "b", "c"]
        str_result = PaginatedResult[str].create(str_items, total=5, page=1, size=3)
        assert str_result.items == str_items


class TestPaginationResponse:
    """Test PaginationResponse functionality."""

    def test_pagination_response_creation(self) -> None:
        """Test PaginationResponse basic creation."""
        paginated_data = PaginatedResult.create(
            items=[{"id": 1}], total=5, page=1, size=1
        )
        response = PaginationResponse(
            data=paginated_data, success=True, message="Success"
        )

        assert response.data == paginated_data
        assert response.success is True
        assert response.message == "Success"

    def test_pagination_response_default_values(self) -> None:
        """Test PaginationResponse with default values."""
        paginated_data = PaginatedResult.create(items=[], total=0, page=1, size=10)
        response = PaginationResponse(data=paginated_data)

        assert response.success is True
        assert response.message is None

    def test_pagination_response_from_page(self) -> None:
        """Test PaginationResponse creation from fastapi-pagination Page."""
        items = [{"id": 1}, {"id": 2}]
        # Create a mock Page object
        page = MagicMock()
        page.items = items
        page.total = 5
        page.page = 1
        page.size = 2
        page.pages = 3

        response = PaginationResponse.from_page(page, "Items retrieved successfully")

        assert response.data.items == items
        assert response.data.total == 5
        assert response.data.page == 1
        assert response.data.size == 2
        assert response.data.pages == 3
        assert response.success is True
        assert response.message == "Items retrieved successfully"

    def test_pagination_response_from_page_no_message(self) -> None:
        """Test PaginationResponse from Page without message."""
        items = [{"id": 1}]
        # Create a mock Page object
        page = MagicMock()
        page.items = items
        page.total = 1
        page.page = 1
        page.size = 1
        page.pages = 1

        response = PaginationResponse.from_page(page)

        assert response.data.items == items
        assert response.message is None

    def test_pagination_response_create(self) -> None:
        """Test PaginationResponse.create with automatic pagination."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginationResponse.create(
            items=items, total=10, page=1, size=3, message="Items found"
        )

        assert response.data.items == items
        assert response.data.total == 10
        assert response.data.page == 1
        assert response.data.size == 3
        assert response.data.pages == 4  # (10 + 3 - 1) // 3 = 4
        assert response.success is True
        assert response.message == "Items found"

    def test_pagination_response_create_no_message(self) -> None:
        """Test PaginationResponse.create without message."""
        items = [{"id": 1}]
        response = PaginationResponse.create(items=items, total=1, page=1, size=1)

        assert response.data.items == items
        assert response.message is None

    def test_pagination_response_serialization(self) -> None:
        """Test PaginationResponse serialization."""
        items = [{"id": 1}, {"id": 2}]
        response = PaginationResponse.create(
            items=items, total=5, page=1, size=2, message="Success"
        )
        data = response.model_dump()

        assert data["data"]["items"] == items
        assert data["data"]["total"] == 5
        assert data["success"] is True
        assert data["message"] == "Success"

    def test_pagination_response_generic_type_safety(self) -> None:
        """Test PaginationResponse generic type safety."""
        # Test with different types
        int_items = [1, 2, 3]
        int_response = PaginationResponse[int].create(
            int_items, total=10, page=1, size=3
        )
        assert int_response.data.items == int_items

        str_items = ["a", "b"]
        str_response = PaginationResponse[str].create(
            str_items, total=5, page=1, size=2
        )
        assert str_response.data.items == str_items


class TestPaginationConvenienceFunctions:
    """Test pagination convenience functions."""

    def test_create_pagination_params_default(self) -> None:
        """Test create_pagination_params with default values."""
        params = create_pagination_params()

        assert isinstance(params, Params)
        assert params.page == 1
        assert params.size == 10

    def test_create_pagination_params_custom(self) -> None:
        """Test create_pagination_params with custom values."""
        params = create_pagination_params(page=5, size=25)

        assert isinstance(params, Params)
        assert params.page == 5
        assert params.size == 25

    def test_create_paginated_response(self) -> None:
        """Test create_paginated_response function."""
        items = [{"id": 1}, {"id": 2}]
        response = create_paginated_response(
            items=items, total=5, page=1, size=2, message="Items retrieved"
        )

        assert isinstance(response, PaginationResponse)
        assert response.data.items == items
        assert response.data.total == 5
        assert response.data.page == 1
        assert response.data.size == 2
        assert response.data.pages == 3  # (5 + 2 - 1) // 2 = 3
        assert response.success is True
        assert response.message == "Items retrieved"

    def test_create_paginated_response_no_message(self) -> None:
        """Test create_paginated_response without message."""
        items = [{"id": 1}]
        response = create_paginated_response(items=items, total=1, page=1, size=1)

        assert response.data.items == items
        assert response.message is None


class TestPaginationIntegration:
    """Integration tests for pagination models."""

    def test_full_pagination_flow(self) -> None:
        """Test complete pagination flow from request to response."""
        # Step 1: Create pagination request
        request = PaginationRequest(page=2, size=3)
        params = request.to_params()

        # Step 2: Simulate fastapi-pagination Page (what would come from database)
        items = [{"id": 4}, {"id": 5}, {"id": 6}]
        page = MagicMock()
        page.items = items
        page.total = 10
        page.page = 2
        page.size = 3
        page.pages = 4

        # Step 3: Convert to our PaginatedResult
        paginated_result = PaginatedResult.from_page(page)

        # Step 4: Create final response
        response = PaginationResponse.from_page(page, "Page 2 of 4")

        # Assertions
        assert params.page == 2
        assert params.size == 3
        assert paginated_result.items == items
        assert paginated_result.total == 10
        assert paginated_result.page == 2
        assert paginated_result.size == 3
        assert paginated_result.pages == 4
        assert response.data == paginated_result
        assert response.success is True
        assert response.message == "Page 2 of 4"

    def test_pagination_edge_cases(self) -> None:
        """Test pagination edge cases."""
        # Empty result set
        empty_response = PaginationResponse.create(items=[], total=0, page=1, size=10)
        assert empty_response.data.items == []
        assert empty_response.data.pages == 0

        # Single page with exact items
        exact_response = PaginationResponse.create(
            items=[{"id": 1}, {"id": 2}], total=2, page=1, size=2
        )
        assert exact_response.data.pages == 1

        # Last page with remaining items
        last_page_response = PaginationResponse.create(
            items=[{"id": 9}, {"id": 10}], total=10, page=5, size=2
        )
        assert last_page_response.data.pages == 5  # (10 + 2 - 1) // 2 = 5
