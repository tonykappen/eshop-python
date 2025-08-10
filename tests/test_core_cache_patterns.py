"""Comprehensive tests for cache patterns."""

from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from eshop.core.cache.patterns import (
    CacheAsidePattern,
    CacheInvalidationPattern,
    CacheKeyBuilder,
    ICacheService,
)


class MockCacheService(ICacheService):
    """Mock cache service for testing."""

    def __init__(self):
        self.cache_data = {}
        self.get_calls = []
        self.set_calls = []
        self.delete_calls = []
        self.exists_calls = []
        self.invalidate_pattern_calls = []

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        self.get_calls.append(key)
        return self.cache_data.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        self.set_calls.append((key, value, ttl))
        self.cache_data[key] = value

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self.delete_calls.append(key)
        if key in self.cache_data:
            del self.cache_data[key]

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        self.exists_calls.append(key)
        return key in self.cache_data

    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern."""
        self.invalidate_pattern_calls.append(pattern)
        # Simple pattern matching for testing
        keys_to_delete = []
        for key in self.cache_data:
            if pattern.replace("*", "") in key:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.cache_data[key]


class TestICacheService:
    """Test ICacheService interface."""

    def test_icache_service_is_abstract(self) -> None:
        """Test that ICacheService is an abstract base class."""
        with pytest.raises(TypeError):
            ICacheService()  # Should raise TypeError for abstract class


class TestCacheAsidePattern:
    """Test CacheAsidePattern functionality."""

    @pytest.fixture
    def mock_cache_service(self) -> MockCacheService:
        """Provide mock cache service."""
        return MockCacheService()

    @pytest.fixture
    def cache_aside_pattern(self, mock_cache_service: MockCacheService) -> CacheAsidePattern:
        """Provide CacheAsidePattern instance."""
        return CacheAsidePattern(mock_cache_service)

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, cache_aside_pattern: CacheAsidePattern, mock_cache_service: MockCacheService) -> None:
        """Test get_or_set when value exists in cache."""
        # Setup: Value exists in cache
        test_key = "test:key"
        test_value = {"data": "cached_value"}
        mock_cache_service.cache_data[test_key] = test_value

        # Mock fetch function (should not be called)
        fetch_func = AsyncMock()

        # Execute
        result = await cache_aside_pattern.get_or_set(test_key, fetch_func)

        # Assert
        assert result == test_value
        assert mock_cache_service.get_calls == [test_key]
        fetch_func.assert_not_called()
        assert len(mock_cache_service.set_calls) == 0

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, cache_aside_pattern: CacheAsidePattern, mock_cache_service: MockCacheService) -> None:
        """Test get_or_set when value doesn't exist in cache."""
        # Setup: Value doesn't exist in cache
        test_key = "test:key"
        test_value = {"data": "fetched_value"}

        # Mock fetch function
        fetch_func = AsyncMock(return_value=test_value)

        # Execute
        result = await cache_aside_pattern.get_or_set(test_key, fetch_func)

        # Assert
        assert result == test_value
        assert mock_cache_service.get_calls == [test_key]
        fetch_func.assert_called_once()
        assert len(mock_cache_service.set_calls) == 1
        assert mock_cache_service.set_calls[0][0] == test_key
        assert mock_cache_service.set_calls[0][1] == test_value
        assert mock_cache_service.set_calls[0][2] is None  # No TTL

    @pytest.mark.asyncio
    async def test_get_or_set_with_ttl(self, cache_aside_pattern: CacheAsidePattern, mock_cache_service: MockCacheService) -> None:
        """Test get_or_set with TTL parameter."""
        # Setup: Value doesn't exist in cache
        test_key = "test:key"
        test_value = {"data": "fetched_value"}
        test_ttl = 300

        # Mock fetch function
        fetch_func = AsyncMock(return_value=test_value)

        # Execute
        result = await cache_aside_pattern.get_or_set(test_key, fetch_func, test_ttl)

        # Assert
        assert result == test_value
        assert mock_cache_service.set_calls[0][2] == test_ttl

    @pytest.mark.asyncio
    async def test_get_or_set_none_value(self, cache_aside_pattern: CacheAsidePattern, mock_cache_service: MockCacheService) -> None:
        """Test get_or_set when fetch function returns None."""
        # Setup: Fetch function returns None
        test_key = "test:key"

        # Mock fetch function returning None
        fetch_func = AsyncMock(return_value=None)

        # Execute
        result = await cache_aside_pattern.get_or_set(test_key, fetch_func)

        # Assert
        assert result is None
        fetch_func.assert_called_once()
        assert len(mock_cache_service.set_calls) == 0  # Should not cache None values

    @pytest.mark.asyncio
    async def test_invalidate_and_refetch(self, cache_aside_pattern: CacheAsidePattern, mock_cache_service: MockCacheService) -> None:
        """Test invalidate_and_refetch functionality."""
        # Setup: Value exists in cache
        test_key = "test:key"
        old_value = {"data": "old_value"}
        new_value = {"data": "new_value"}
        mock_cache_service.cache_data[test_key] = old_value

        # Mock fetch function
        fetch_func = AsyncMock(return_value=new_value)

        # Execute
        result = await cache_aside_pattern.invalidate_and_refetch(test_key, fetch_func)

        # Assert
        assert result == new_value
        assert mock_cache_service.delete_calls == [test_key]
        fetch_func.assert_called_once()
        assert len(mock_cache_service.set_calls) == 1
        assert mock_cache_service.set_calls[0][1] == new_value


class TestCacheInvalidationPattern:
    """Test CacheInvalidationPattern functionality."""

    @pytest.fixture
    def mock_cache_service(self) -> MockCacheService:
        """Provide mock cache service."""
        return MockCacheService()

    @pytest.fixture
    def cache_invalidation_pattern(self, mock_cache_service: MockCacheService) -> CacheInvalidationPattern:
        """Provide CacheInvalidationPattern instance."""
        return CacheInvalidationPattern(mock_cache_service)

    @pytest.mark.asyncio
    async def test_invalidate_entity(self, cache_invalidation_pattern: CacheInvalidationPattern, mock_cache_service: MockCacheService) -> None:
        """Test invalidate_entity functionality."""
        # Setup: Add some test data
        entity_id = uuid4()
        mock_cache_service.cache_data[f"product:{entity_id}:details"] = {"name": "Test Product"}
        mock_cache_service.cache_data[f"product:{entity_id}:price"] = {"price": 99.99}
        mock_cache_service.cache_data["product:other:details"] = {"name": "Other Product"}

        # Execute
        await cache_invalidation_pattern.invalidate_entity("product", entity_id)

        # Assert
        assert len(mock_cache_service.invalidate_pattern_calls) == 1
        assert mock_cache_service.invalidate_pattern_calls[0] == f"product:{entity_id}:*"
        assert "product:other:details" in mock_cache_service.cache_data  # Should remain
        assert f"product:{entity_id}:details" not in mock_cache_service.cache_data  # Should be deleted
        assert f"product:{entity_id}:price" not in mock_cache_service.cache_data  # Should be deleted

    @pytest.mark.asyncio
    async def test_invalidate_collection(self, cache_invalidation_pattern: CacheInvalidationPattern, mock_cache_service: MockCacheService) -> None:
        """Test invalidate_collection functionality."""
        # Setup: Add some test data
        mock_cache_service.cache_data["product:collection"] = {"products": []}
        mock_cache_service.cache_data["product:collection:filtered"] = {"products": []}
        mock_cache_service.cache_data["user:collection"] = {"users": []}

        # Execute
        await cache_invalidation_pattern.invalidate_collection("product")

        # Assert
        assert len(mock_cache_service.invalidate_pattern_calls) == 1
        assert mock_cache_service.invalidate_pattern_calls[0] == "product:*"
        assert "user:collection" in mock_cache_service.cache_data  # Should remain
        assert "product:collection" not in mock_cache_service.cache_data  # Should be deleted
        assert "product:collection:filtered" not in mock_cache_service.cache_data  # Should be deleted

    @pytest.mark.asyncio
    async def test_invalidate_user_data(self, cache_invalidation_pattern: CacheInvalidationPattern, mock_cache_service: MockCacheService) -> None:
        """Test invalidate_user_data functionality."""
        # Setup: Add some test data
        user_id = uuid4()
        mock_cache_service.cache_data[f"user:{user_id}:profile"] = {"name": "John Doe"}
        mock_cache_service.cache_data[f"user:{user_id}:preferences"] = {"theme": "dark"}
        mock_cache_service.cache_data["user:other:profile"] = {"name": "Jane Doe"}

        # Execute
        await cache_invalidation_pattern.invalidate_user_data(user_id)

        # Assert
        assert len(mock_cache_service.invalidate_pattern_calls) == 1
        assert mock_cache_service.invalidate_pattern_calls[0] == f"user:{user_id}:*"
        assert "user:other:profile" in mock_cache_service.cache_data  # Should remain
        assert f"user:{user_id}:profile" not in mock_cache_service.cache_data  # Should be deleted
        assert f"user:{user_id}:preferences" not in mock_cache_service.cache_data  # Should be deleted

    @pytest.mark.asyncio
    async def test_invalidate_related_data(self, cache_invalidation_pattern: CacheInvalidationPattern, mock_cache_service: MockCacheService) -> None:
        """Test invalidate_related_data functionality."""
        # Setup: Add some test data
        entity_id = uuid4()
        mock_cache_service.cache_data[f"product:{entity_id}:details"] = {"name": "Test Product"}
        mock_cache_service.cache_data[f"category:*:{entity_id}:products"] = {"products": []}
        mock_cache_service.cache_data[f"brand:*:{entity_id}:products"] = {"products": []}
        mock_cache_service.cache_data["product:other:details"] = {"name": "Other Product"}

        # Execute
        await cache_invalidation_pattern.invalidate_related_data(
            "product", entity_id, ["category", "brand"]
        )

        # Assert
        assert len(mock_cache_service.invalidate_pattern_calls) == 3
        assert f"product:{entity_id}:*" in mock_cache_service.invalidate_pattern_calls
        assert f"category:*:{entity_id}:*" in mock_cache_service.invalidate_pattern_calls
        assert f"brand:*:{entity_id}:*" in mock_cache_service.invalidate_pattern_calls
        assert "product:other:details" in mock_cache_service.cache_data  # Should remain


class TestCacheKeyBuilder:
    """Test CacheKeyBuilder functionality."""

    def test_entity_key_basic(self) -> None:
        """Test entity_key with basic parameters."""
        entity_id = uuid4()
        key = CacheKeyBuilder.entity_key("product", entity_id)
        assert key == f"product:{entity_id}"

    def test_entity_key_with_suffix(self) -> None:
        """Test entity_key with suffix parameter."""
        entity_id = uuid4()
        key = CacheKeyBuilder.entity_key("product", entity_id, "details")
        assert key == f"product:{entity_id}:details"

    def test_collection_key_basic(self) -> None:
        """Test collection_key with basic parameters."""
        key = CacheKeyBuilder.collection_key("product")
        assert key == "product:collection"

    def test_collection_key_with_filters(self) -> None:
        """Test collection_key with filters."""
        filters = {"category": "electronics", "price_min": "100"}
        key = CacheKeyBuilder.collection_key("product", filters)
        # Should be sorted for consistent key generation
        assert key == "product:collection:category=electronics:price_min=100"

    def test_collection_key_with_filters_none(self) -> None:
        """Test collection_key with None filters."""
        key = CacheKeyBuilder.collection_key("product", None)
        assert key == "product:collection"

    def test_collection_key_with_empty_filters(self) -> None:
        """Test collection_key with empty filters."""
        key = CacheKeyBuilder.collection_key("product", {})
        assert key == "product:collection"

    def test_user_key(self) -> None:
        """Test user_key functionality."""
        user_id = uuid4()
        key = CacheKeyBuilder.user_key(user_id, "profile")
        assert key == f"user:{user_id}:profile"

    def test_collection_key_filters_sorting(self) -> None:
        """Test that collection_key sorts filters for consistent key generation."""
        filters = {"z": "last", "a": "first", "m": "middle"}
        key = CacheKeyBuilder.collection_key("product", filters)
        # Should be sorted alphabetically
        assert key == "product:collection:a=first:m=middle:z=last"


class TestCachePatternsIntegration:
    """Integration tests for cache patterns."""

    @pytest.fixture
    def mock_cache_service(self) -> MockCacheService:
        """Provide mock cache service."""
        return MockCacheService()

    @pytest.fixture
    def cache_aside_pattern(self, mock_cache_service: MockCacheService) -> CacheAsidePattern:
        """Provide CacheAsidePattern instance."""
        return CacheAsidePattern(mock_cache_service)

    @pytest.fixture
    def cache_invalidation_pattern(self, mock_cache_service: MockCacheService) -> CacheInvalidationPattern:
        """Provide CacheInvalidationPattern instance."""
        return CacheInvalidationPattern(mock_cache_service)

    @pytest.mark.asyncio
    async def test_cache_aside_with_invalidation_integration(
        self,
        cache_aside_pattern: CacheAsidePattern,
        cache_invalidation_pattern: CacheInvalidationPattern,
        mock_cache_service: MockCacheService
    ) -> None:
        """Test integration between cache aside and invalidation patterns."""
        # Setup
        entity_id = uuid4()
        cache_key = CacheKeyBuilder.entity_key("product", entity_id, "details")
        test_value = {"name": "Test Product", "price": 99.99}

        # Mock fetch function
        fetch_func = AsyncMock(return_value=test_value)

        # Step 1: Get or set (should fetch and cache)
        result1 = await cache_aside_pattern.get_or_set(cache_key, fetch_func)
        assert result1 == test_value
        assert mock_cache_service.cache_data[cache_key] == test_value

        # Step 2: Invalidate entity
        await cache_invalidation_pattern.invalidate_entity("product", entity_id)
        assert cache_key not in mock_cache_service.cache_data

        # Step 3: Get or set again (should fetch again)
        fetch_func.reset_mock()
        result2 = await cache_aside_pattern.get_or_set(cache_key, fetch_func)
        assert result2 == test_value
        fetch_func.assert_called_once()  # Should be called again
        assert mock_cache_service.cache_data[cache_key] == test_value
