"""Invalid price exception."""

from app.core.exceptions.common_exceptions import DomainException


class InvalidPrice(DomainException):
    """Exception raised when a product price is invalid."""

    def __init__(self, price: str, reason: str = ""):
        """
        Initialize the exception.
        
        Args:
            price: The invalid price
            reason: Reason why the price is invalid
        """
        self.price = price
        self.reason = reason
        message = f"Invalid price: {price}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class NegativePrice(DomainException):
    """Exception raised when a product price is negative."""

    def __init__(self, price: str):
        """
        Initialize the exception.
        
        Args:
            price: The negative price
        """
        self.price = price
        super().__init__(f"Price cannot be negative: {price}")


class ZeroPrice(DomainException):
    """Exception raised when a product price is zero."""

    def __init__(self):
        """Initialize the exception."""
        super().__init__("Price cannot be zero")


