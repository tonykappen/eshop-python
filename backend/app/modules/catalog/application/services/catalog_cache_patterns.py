"""Cache key naming patterns for catalog module."""

from uuid import UUID


class CatalogCachePatterns:
    """Cache key naming patterns for catalog entities."""

    @staticmethod
    def product_key(product_id: UUID) -> str:
        """
        Generate cache key for a product by ID.
        
        Args:
            product_id: Product UUID
            
        Returns:
            Cache key string
        """
        return f"product:{product_id}"

    @staticmethod
    def product_list_key(category: str | None = None, page: int = 1, page_size: int = 10) -> str:
        """
        Generate cache key for product list.
        
        Args:
            category: Optional category filter
            page: Page number
            page_size: Page size
            
        Returns:
            Cache key string
        """
        if category:
            return f"list:products:category:{category}:page:{page}:size:{page_size}"
        return f"list:products:page:{page}:size:{page_size}"

    @staticmethod
    def category_key(category_id: UUID) -> str:
        """
        Generate cache key for a category by ID.
        
        Args:
            category_id: Category UUID
            
        Returns:
            Cache key string
        """
        return f"category:{category_id}"

    @staticmethod
    def category_list_key() -> str:
        """
        Generate cache key for category list.
        
        Returns:
            Cache key string
        """
        return "list:categories"

    @staticmethod
    def inventory_key(product_id: UUID) -> str:
        """
        Generate cache key for inventory by product ID.
        
        Args:
            product_id: Product UUID
            
        Returns:
            Cache key string
        """
        return f"inventory:{product_id}"

    @staticmethod
    def invalidate_product_pattern(product_id: UUID | None = None) -> str:
        """
        Generate cache invalidation pattern for products.
        
        Args:
            product_id: Optional specific product ID
            
        Returns:
            Cache pattern string for invalidation
        """
        if product_id:
            return f"product:{product_id}*"
        return "product:*"

    @staticmethod
    def invalidate_product_list_pattern() -> str:
        """
        Generate cache invalidation pattern for product lists.
        
        Returns:
            Cache pattern string for invalidation
        """
        return "list:products:*"

    @staticmethod
    def invalidate_category_pattern(category_id: UUID | None = None) -> str:
        """
        Generate cache invalidation pattern for categories.
        
        Args:
            category_id: Optional specific category ID
            
        Returns:
            Cache pattern string for invalidation
        """
        if category_id:
            return f"category:{category_id}*"
        return "category:*"


