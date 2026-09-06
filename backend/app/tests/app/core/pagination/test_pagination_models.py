"""Tests for pagination models."""

from app.core.pagination.models import (
    PaginatedResult,
    PaginationRequest,
    PaginationResponse,
    create_paginated_response,
    create_pagination_params,
)


class TestPaginationModels:
    def test_pagination_request_to_params(self) -> None:
        request = PaginationRequest(page=2, size=25)
        params = request.to_params()
        assert params.page == 2
        assert params.size == 25

    def test_paginated_result_create(self) -> None:
        result = PaginatedResult.create(
            items=["a", "b"], total=25, page=2, size=10
        )
        assert result.pages == 3
        assert result.total == 25
        assert len(result.items) == 2

    def test_pagination_response_create(self) -> None:
        response = PaginationResponse.create(
            items=[1, 2, 3], total=3, page=1, size=10, message="ok"
        )
        assert response.success is True
        assert response.message == "ok"
        assert response.data.total == 3

    def test_create_pagination_params(self) -> None:
        params = create_pagination_params(page=3, size=5)
        assert params.page == 3
        assert params.size == 5

    def test_create_paginated_response(self) -> None:
        response = create_paginated_response(
            items=["x"], total=1, page=1, size=10, message="done"
        )
        assert response.data.items == ["x"]
        assert response.message == "done"
