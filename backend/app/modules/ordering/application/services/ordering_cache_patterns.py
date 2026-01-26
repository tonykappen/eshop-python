"""Cache key naming patterns for ordering module."""

from uuid import UUID


class OrderingCachePatterns:
    """Cache key naming patterns for orders."""

    @staticmethod
    def order_key(order_id: UUID) -> str:
        """
        Get cache key for a single order.

        Args:
            order_id: Order ID

        Returns:
            Cache key string
        """
        return f"order:{order_id}"

    @staticmethod
    def orders_list_key(page: int, page_size: int) -> str:
        """
        Get cache key for paginated orders list.

        Args:
            page: Page number
            page_size: Page size

        Returns:
            Cache key string
        """
        return f"orders:list:{page}:{page_size}"

    @staticmethod
    def orders_list_by_customer_key(customer_id: UUID, page: int, page_size: int) -> str:
        """
        Get cache key for paginated orders list by customer.

        Args:
            customer_id: Customer ID
            page: Page number
            page_size: Page size

        Returns:
            Cache key string
        """
        return f"orders:customer:{customer_id}:{page}:{page_size}"
