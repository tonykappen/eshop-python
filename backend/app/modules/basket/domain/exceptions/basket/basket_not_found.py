"""Basket not found exception."""

from app.core.exceptions.common_exceptions import DomainException


class BasketNotFoundException(DomainException):
    """Exception raised when a basket is not found."""

    def __init__(self, user_name: str):
        """
        Initialize the exception.

        Args:
            user_name: The user name whose basket was not found
        """
        self.user_name = user_name
        super().__init__(f"Basket for user {user_name} not found")
