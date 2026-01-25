"""Product already exists exception."""

from app.core.exceptions.common_exceptions import DomainException


class ProductAlreadyExists(DomainException):
    """Exception raised when trying to create a product that already exists."""

    def __init__(self, sku: str):
        """
        Initialize the exception.

        Args:
            sku: The SKU of the product that already exists
        """
        self.sku = sku
        super().__init__(f"Product with SKU {sku} already exists")


class ProductWithNameAlreadyExists(DomainException):
    """Exception raised when trying to create a product with a name that already exists."""

    def __init__(self, name: str):
        """
        Initialize the exception.

        Args:
            name: The name of the product that already exists
        """
        self.name = name
        super().__init__(f"Product with name {name} already exists")
