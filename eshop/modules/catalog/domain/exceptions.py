"""Domain exceptions for Catalog module with 1-1 parity to .NET."""

from uuid import UUID

from eshop.core.exceptions.base import NotFoundError


class ProductNotFoundError(NotFoundError):
    """Exception raised when a product is not found - matches .NET ProductNotFoundException."""

    def __init__(self, product_id: UUID) -> None:
        """Initialize exception with product ID."""
        self.product_id = product_id
        super().__init__(f"Product with ID {product_id} was not found")
