"""Basket domain exceptions."""


class BasketNotFoundException(Exception):
    """Exception raised when basket is not found."""
    
    def __init__(self, basket_id: str):
        self.basket_id = basket_id
        super().__init__(f"Basket with ID {basket_id} was not found") 