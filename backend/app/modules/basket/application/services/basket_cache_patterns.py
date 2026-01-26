"""Cache key naming patterns for basket module."""


class BasketCachePatterns:
    """Cache key naming patterns for basket entities."""

    @staticmethod
    def basket_key(user_name: str) -> str:
        """
        Generate cache key for a basket by user name.

        Args:
            user_name: User name

        Returns:
            Cache key string
        """
        return f"basket:{user_name}"

    @staticmethod
    def invalidate_basket_pattern(user_name: str | None = None) -> str:
        """
        Generate cache invalidation pattern for baskets.

        Args:
            user_name: Optional specific user name

        Returns:
            Cache pattern string for invalidation
        """
        if user_name:
            return f"basket:{user_name}*"
        return "basket:*"
