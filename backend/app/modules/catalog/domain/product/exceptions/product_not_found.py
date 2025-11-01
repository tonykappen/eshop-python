"""Product not found exception."""

from uuid import UUID

from app.core.exceptions.base import DomainException


class ProductNotFound(DomainException):
    """Exception raised when a product is not found."""

    def __init__(self, product_id: UUID):
        """
        Initialize the exception.

        Args:
            product_id: The ID of the product that was not found
        """
        self.product_id = product_id
        super().__init__(f"Product with ID {product_id} not found")


class ProductNotFoundBySku(DomainException):
    """Exception raised when a product is not found by SKU."""

    def __init__(self, sku: str):
        """
        Initialize the exception.

        Args:
            sku: The SKU of the product that was not found
        """
        self.sku = sku
        super().__init__(f"Product with SKU {sku} not found")


class ProductNotFoundByName(DomainException):
    """Exception raised when a product is not found by name."""

    def __init__(self, name: str):
        """
        Initialize the exception.

        Args:
            name: The name of the product that was not found
        """
        self.name = name
        super().__init__(f"Product with name {name} not found")
