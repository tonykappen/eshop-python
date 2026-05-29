"""Tests for Redis cache service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.core.cache.redis_cache_service import RedisCacheService


@pytest.fixture
def mock_redis() -> AsyncMock:
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.exists = AsyncMock(return_value=1)
    client.ping = AsyncMock(return_value=True)
    client.close = AsyncMock()
    client.aclose = AsyncMock()
    client.scan_iter = AsyncMock(return_value=iter([]))
    return client


@pytest.fixture
def cache(mock_redis: AsyncMock) -> RedisCacheService:
    service = RedisCacheService(redis_client=mock_redis, default_ttl=60)
    service._is_connected = True
    return service


@pytest.mark.asyncio
async def test_get_returns_none_for_missing_key(cache: RedisCacheService) -> None:
    assert await cache.get("missing") is None


@pytest.mark.asyncio
async def test_get_deserializes_json(
    cache: RedisCacheService, mock_redis: AsyncMock
) -> None:
    mock_redis.get.return_value = '{"name": "widget"}'
    assert await cache.get("product:1") == {"name": "widget"}


@pytest.mark.asyncio
async def test_set_serializes_dict(
    cache: RedisCacheService, mock_redis: AsyncMock
) -> None:
    await cache.set("product:1", {"price": 10})
    mock_redis.setex.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_and_exists(cache: RedisCacheService, mock_redis: AsyncMock) -> None:
    await cache.delete("key")
    assert await cache.exists("key") is True
    mock_redis.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_ping(cache: RedisCacheService, mock_redis: AsyncMock) -> None:
    assert await cache.ping() is True


@pytest.mark.asyncio
async def test_get_many_and_set_many(cache: RedisCacheService, mock_redis: AsyncMock) -> None:
    mock_redis.mget = AsyncMock(return_value=['{"a": 1}', None])
    mock_pipeline = AsyncMock()
    mock_pipeline.setex = MagicMock(return_value=mock_pipeline)
    mock_pipeline.execute = AsyncMock(return_value=[True])
    mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

    result = await cache.get_many(["k1", "k2"])
    assert result["k1"] == {"a": 1}
    assert "k2" not in result

    await cache.set_many({"k1": {"x": 1}}, ttl=30)
    mock_pipeline.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_close(cache: RedisCacheService, mock_redis: AsyncMock) -> None:
    await cache.close()
    mock_redis.close.assert_awaited_once()
    mock_redis.aclose.assert_awaited_once()
