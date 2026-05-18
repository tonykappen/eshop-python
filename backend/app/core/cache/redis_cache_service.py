"""Redis-based cache implementation."""

import json
from typing import Any

import redis.asyncio as redis
from app.config.settings import settings
from app.core.cache.patterns import ICacheService
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class RedisCacheService(ICacheService):
    """
    Redis-based cache implementation.

    Implements ICacheService interface using Redis as the backing store.
    Provides JSON serialization/deserialization and error handling.
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        connection_string: str | None = None,
        default_ttl: int = 3600,
    ):
        """
        Initialize Redis cache service.

        Args:
            redis_client: Optional pre-configured Redis client
            connection_string: Optional Redis connection string (defaults to settings)
            default_ttl: Default TTL in seconds (default: 3600 = 1 hour)
        """
        self._redis_client = redis_client
        self._connection_string = connection_string or settings.redis_connection_string
        self._default_ttl = default_ttl
        self._is_connected = False

    @property
    def redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis_client is None:
            self._redis_client = self._create_redis_client()
        return self._redis_client

    def _create_redis_client(self) -> redis.Redis:
        """
        Create Redis client with configuration.

        Returns:
            Configured Redis async client
        """
        try:
            client = redis.Redis.from_url(
                self._connection_string,
                decode_responses=True,
                encoding="utf-8",
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self._is_connected = True
            logger.log_with_context(
                "Redis cache service initialized",
                "info",
                context={"connection_string": self._connection_string},
            )
            return client
        except Exception as e:
            logger.log_error_with_context(
                "Failed to create Redis client",
                error=e,
                context={"connection_string": self._connection_string},
            )
            raise

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None

            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, return as string
                return value
        except redis.ConnectionError as e:
            logger.log_error_with_context(
                f"Redis connection error while getting key {key}",
                error=e,
            )
            return None
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to get cache key {key}",
                error=e,
            )
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if not string)
            ttl: Time to live in seconds (defaults to default_ttl)
        """
        try:
            # Serialize value to JSON if it's not a string
            if isinstance(value, str):
                serialized_value = value
            else:
                serialized_value = json.dumps(value, default=str)

            ttl = ttl or self._default_ttl
            await self.redis_client.setex(key, ttl, serialized_value)
            logger.log_debug_with_context(
                f"Cached key {key} with TTL {ttl}",
                context={"key": key, "ttl": ttl},
            )
        except redis.ConnectionError as e:
            logger.log_error_with_context(
                f"Redis connection error while setting key {key}",
                error=e,
            )
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to set cache key {key}",
                error=e,
            )

    async def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key to delete
        """
        try:
            result = await self.redis_client.delete(key)
            if result:
                logger.log_debug_with_context(
                    f"Deleted cache key {key}",
                    context={"key": key},
                )
        except redis.ConnectionError as e:
            logger.log_error_with_context(
                f"Redis connection error while deleting key {key}",
                error=e,
            )
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to delete cache key {key}",
                error=e,
            )

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except redis.ConnectionError as e:
            logger.log_error_with_context(
                f"Redis connection error while checking key {key}",
                error=e,
            )
            return False
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to check cache key {key}",
                error=e,
            )
            return False

    async def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Redis key pattern (supports wildcards like *)

        Note:
            Using KEYS command can be slow on large datasets.
            Consider using SCAN for production with many keys.
        """
        try:
            # Use SCAN instead of KEYS for better performance on large datasets
            keys_to_delete = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys_to_delete.append(key)
                # Delete in batches to avoid memory issues
                if len(keys_to_delete) >= 100:
                    await self.redis_client.delete(*keys_to_delete)
                    logger.log_debug_with_context(
                        f"Deleted batch of {len(keys_to_delete)} keys matching pattern {pattern}",
                        context={"pattern": pattern, "count": len(keys_to_delete)},
                    )
                    keys_to_delete = []

            # Delete remaining keys
            if keys_to_delete:
                await self.redis_client.delete(*keys_to_delete)
                logger.log_debug_with_context(
                    f"Deleted {len(keys_to_delete)} keys matching pattern {pattern}",
                    context={"pattern": pattern, "count": len(keys_to_delete)},
                )
        except redis.ConnectionError as e:
            logger.log_error_with_context(
                f"Redis connection error while invalidating pattern {pattern}",
                error=e,
            )
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to invalidate pattern {pattern}",
                error=e,
            )

    async def close(self) -> None:
        """Close Redis connection gracefully."""
        if self._redis_client and self._is_connected:
            try:
                await self._redis_client.close()
                await self._redis_client.aclose()  # Close async connection pool
                self._is_connected = False
                logger.log_with_context(
                    "Redis cache service connection closed",
                    "info",
                )
            except Exception as e:
                logger.log_error_with_context(
                    "Failed to close Redis connection",
                    error=e,
                )

    async def ping(self) -> bool:
        """
        Ping Redis server to check connectivity.

        Returns:
            True if Redis is reachable, False otherwise
        """
        try:
            result = await self.redis_client.ping()
            return result is True
        except Exception as e:
            logger.log_warning_with_context(
                "Redis ping failed",
                context={"error": str(e)},
            )
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (only includes found keys)
        """
        if not keys:
            return {}

        try:
            values = await self.redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values, strict=False):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value
            return result
        except Exception as e:
            logger.log_error_with_context(
                "Failed to get multiple cache keys",
                error=e,
                context={"key_count": len(keys)},
            )
            return {}

    async def set_many(self, mapping: dict[str, Any], ttl: int | None = None) -> None:
        """
        Set multiple values in cache.

        Args:
            mapping: Dictionary of key-value pairs to cache
            ttl: Time to live in seconds (defaults to default_ttl)
        """
        if not mapping:
            return

        try:
            ttl = ttl or self._default_ttl
            pipeline = self.redis_client.pipeline()

            for key, value in mapping.items():
                if isinstance(value, str):
                    serialized_value = value
                else:
                    serialized_value = json.dumps(value, default=str)
                pipeline.setex(key, ttl, serialized_value)

            await pipeline.execute()
            logger.log_debug_with_context(
                f"Cached {len(mapping)} keys with TTL {ttl}",
                context={"key_count": len(mapping), "ttl": ttl},
            )
        except Exception as e:
            logger.log_error_with_context(
                "Failed to set multiple cache keys",
                error=e,
                context={"key_count": len(mapping)},
            )

    def __del__(self) -> None:
        """Cleanup on deletion."""
        # Note: This is a fallback - prefer explicit close() call
        if self._redis_client and self._is_connected:
            try:
                # Use asyncio to close if event loop is available
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule close for later
                        asyncio.create_task(self.close())
                    else:
                        loop.run_until_complete(self.close())
                except RuntimeError:
                    # No event loop available
                    pass
            except Exception:
                pass
