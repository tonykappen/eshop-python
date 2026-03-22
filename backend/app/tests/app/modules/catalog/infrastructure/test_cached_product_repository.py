"""Test Redis caching integration for catalog module."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.catalog.application.services.catalog_cache_service import (
    CatalogCachePatterns,
    CatalogCacheService,
    RedisCacheService,
)


class TestRedisCacheService:
    """Test Redis cache service functionality."""

    @pytest.fixture
    def redis_cache_service(self):
        """Create Redis cache service with mocked Redis client."""
        with patch(
            "app.modules.catalog.application.services.catalog_cache_service.redis.Redis.from_url"
        ) as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            service = RedisCacheService()
            service.redis_client = mock_client
            return service

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, redis_cache_service):
        """Test cache hit scenario."""
        # Arrange
        key = "test:key"
        expected_value = {"id": "123", "name": "Test Product"}
        redis_cache_service.redis_client.get.return_value = (
            '{"id": "123", "name": "Test Product"}'
        )

        # Act
        result = await redis_cache_service.get(key)

        # Assert
        assert result == expected_value
        redis_cache_service.redis_client.get.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, redis_cache_service):
        """Test cache miss scenario."""
        # Arrange
        key = "test:key"
        redis_cache_service.redis_client.get.return_value = None

        # Act
        result = await redis_cache_service.get(key)

        # Assert
        assert result is None
        redis_cache_service.redis_client.get.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_set_cache_value(self, redis_cache_service):
        """Test setting cache value."""
        # Arrange
        key = "test:key"
        value = {"id": "123", "name": "Test Product"}
        ttl = 3600

        # Act
        await redis_cache_service.set(key, value, ttl)

        # Assert
        redis_cache_service.redis_client.setex.assert_called_once_with(
            key, ttl, '{"id": "123", "name": "Test Product"}'
        )

    @pytest.mark.asyncio
    async def test_delete_cache_value(self, redis_cache_service):
        """Test deleting cache value."""
        # Arrange
        key = "test:key"

        # Act
        await redis_cache_service.delete(key)

        # Assert
        redis_cache_service.redis_client.delete.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, redis_cache_service):
        """Test invalidating cache pattern via SCAN + pipeline delete."""
        # Arrange
        pattern = "test:*"
        keys = ["test:key1", "test:key2"]
        mock_pipe = MagicMock()
        mock_pipe.execute = AsyncMock()
        redis_cache_service.redis_client.pipeline = MagicMock(return_value=mock_pipe)
        redis_cache_service.redis_client.scan = AsyncMock(return_value=(0, keys))

        # Act
        await redis_cache_service.invalidate_pattern(pattern)

        # Assert
        redis_cache_service.redis_client.scan.assert_called()
        mock_pipe.delete.assert_any_call("test:key1")
        mock_pipe.delete.assert_any_call("test:key2")
        mock_pipe.execute.assert_awaited_once()
        redis_cache_service.redis_client.pipeline.assert_called_once()


class TestCatalogCacheService:
    """Test catalog-specific cache service functionality."""

    @pytest.fixture
    def catalog_cache_service(self):
        """Create catalog cache service with mocked Redis cache service."""
        mock_redis_service = AsyncMock()
        return CatalogCacheService(mock_redis_service)

    @pytest.mark.asyncio
    async def test_get_product_cache_hit(self, catalog_cache_service):
        """Test getting product from cache."""
        # Arrange
        product_id = uuid4()
        expected_product = {
            "id": str(product_id),
            "name": "Test Product",
            "price": 99.99,
            "description": "Test Description",
            "picture_url": "test.jpg",
            "category": ["Electronics"],
        }
        catalog_cache_service.cache.get.return_value = expected_product

        # Act
        result = await catalog_cache_service.get_product(product_id)

        # Assert
        assert result == expected_product
        catalog_cache_service.cache.get.assert_called_once_with(
            f"catalog:product:{product_id}"
        )

    @pytest.mark.asyncio
    async def test_set_product_cache(self, catalog_cache_service):
        """Test setting product in cache."""
        # Arrange
        product_id = uuid4()
        product_data = {
            "id": str(product_id),
            "name": "Test Product",
            "price": 99.99,
            "description": "Test Description",
            "picture_url": "test.jpg",
            "category": ["Electronics"],
        }
        ttl = 3600

        # Act
        await catalog_cache_service.set_product(product_id, product_data, ttl)

        # Assert
        catalog_cache_service.cache.set.assert_called_once_with(
            f"catalog:product:{product_id}", product_data, ttl
        )

    @pytest.mark.asyncio
    async def test_get_products_list_cache_hit(self, catalog_cache_service):
        """Test getting products list from cache."""
        # Arrange
        page = 1
        size = 10
        filters = {"search": "test"}
        expected_result = {
            "items": [{"id": "123", "name": "Test Product"}],
            "total": 1,
            "page": 1,
            "size": 10,
            "pages": 1,
        }
        catalog_cache_service.cache.get.return_value = expected_result

        # Act
        result = await catalog_cache_service.get_products_list(page, size, filters)

        # Assert
        assert result == expected_result
        catalog_cache_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_product(self, catalog_cache_service):
        """Test invalidating product cache."""
        # Arrange
        product_id = uuid4()

        # Act
        await catalog_cache_service.invalidate_product(product_id)

        # Assert
        # The actual implementation invalidates product key and all product lists (2 calls)
        assert catalog_cache_service.cache.invalidate_pattern.call_count == 2
        calls = catalog_cache_service.cache.invalidate_pattern.call_args_list
        # First call: product key
        assert calls[0][0][0] == f"catalog:product:{product_id}"
        # Second call: all product lists
        assert calls[1][0][0] == "catalog:products:list:*"

    @pytest.mark.asyncio
    async def test_invalidate_products_list(self, catalog_cache_service):
        """Test invalidating products list cache."""
        # Act
        await catalog_cache_service.invalidate_products_list()

        # Assert: targeted deletes for pages 1..10 × page sizes (no SCAN)
        assert catalog_cache_service.cache.delete.await_count == 40
        deleted_keys = [
            call.args[0] for call in catalog_cache_service.cache.delete.await_args_list
        ]
        assert (
            CatalogCachePatterns.products_list_key(1, 10, None) in deleted_keys
        )
        assert (
            CatalogCachePatterns.products_list_key(10, 100, None) in deleted_keys
        )
        catalog_cache_service.cache.invalidate_pattern.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalidate_all_catalog(self, catalog_cache_service):
        """Test invalidating all catalog cache."""
        # Act
        await catalog_cache_service.invalidate_all_catalog()

        # Assert
        catalog_cache_service.cache.invalidate_pattern.assert_called_once_with(
            "catalog:*"
        )


class TestCatalogCachePatterns:
    """Test catalog cache key patterns."""

    def test_product_key(self):
        """Test product cache key generation."""
        # CatalogCachePatterns is imported at the top
        product_id = uuid4()
        expected_key = f"catalog:product:{product_id}"
        assert CatalogCachePatterns.product_key(product_id) == expected_key

    def test_products_list_key_no_filters(self):
        """Test products list cache key generation without filters."""
        # CatalogCachePatterns is imported at the top
        page = 1
        size = 10
        expected_key = "catalog:products:list:page:1:size:10"
        assert CatalogCachePatterns.products_list_key(page, size) == expected_key

    def test_products_list_key_with_filters(self):
        """Test products list cache key generation with filters."""
        # CatalogCachePatterns is imported at the top
        page = 1
        size = 10
        filters = {"search": "test", "category": "electronics"}
        expected_key = "catalog:products:list:page:1:size:10:filters:category=electronics:search=test"
        assert (
            CatalogCachePatterns.products_list_key(page, size, filters) == expected_key
        )

    def test_category_key(self):
        """Test category cache key generation."""
        # CatalogCachePatterns is imported at the top
        category_id = uuid4()
        expected_key = f"catalog:category:{category_id}"
        assert CatalogCachePatterns.category_key(category_id) == expected_key

    def test_categories_list_key(self):
        """Test categories list cache key generation."""
        # CatalogCachePatterns is imported at the top
        expected_key = "catalog:categories:list"
        assert CatalogCachePatterns.categories_list_key() == expected_key
