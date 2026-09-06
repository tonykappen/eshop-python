"""Tests for basket domain exceptions."""

from app.modules.basket.domain.exceptions.basket.basket_not_found import \
    BasketNotFoundException


class TestBasketNotFoundException:
    """Test BasketNotFoundException."""

    def test_basket_not_found_exception_initialization(self) -> None:
        """Test BasketNotFoundException initialization."""
        user_name = "testuser"
        exception = BasketNotFoundException(user_name)

        assert exception.user_name == user_name
        assert str(exception) == f"Basket for user {user_name} not found"
        assert "Basket for user" in str(exception)

    def test_basket_not_found_exception_inherits_from_domain_exception(self) -> None:
        """Test that BasketNotFoundException inherits from DomainException."""
        from app.core.exceptions.common_exceptions import DomainException

        exception = BasketNotFoundException("testuser")
        assert isinstance(exception, DomainException)
