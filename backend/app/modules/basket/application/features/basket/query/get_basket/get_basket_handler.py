"""GetBasketHandler with 1-1 parity to .NET implementation."""

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.basket.application.dtos.shopping_cart_dto import (
    ShoppingCartDto, ShoppingCartItemDto)
from app.modules.basket.domain.repositories.basket import IBasketRepository

from .get_basket_query import GetBasketQuery, GetBasketResult


class GetBasketHandler(IRequestHandler[GetBasketQuery, GetBasketResult]):
    """Handler for GetBasketQuery - matches .NET GetBasketHandler."""

    def __init__(self, repository: IBasketRepository) -> None:
        """
        Initialize handler.

        Args:
            repository: Basket repository
        """
        self.repository = repository

    async def handle(
        self, query: GetBasketQuery, cancellation_token: CancellationToken
    ) -> GetBasketResult:
        """
        Handle the query - matches .NET Handle(GetBasketQuery query, CancellationToken cancellationToken).

        Args:
            query: The query to handle
            cancellation_token: Cancellation token

        Returns:
            GetBasketResult containing the shopping cart DTO
        """
        # Check for cancellation
        cancellation_token.throw_if_cancellation_requested()

        # Get basket with user_name (with tracking for read operations)
        # If basket doesn't exist, return an empty basket instead of raising an exception
        # This is a common pattern in e-commerce where baskets are created on first item addition
        from app.modules.basket.domain.exceptions.basket.basket_not_found import \
            BasketNotFoundException

        try:
            basket = await self.repository.get_basket(
                query.user_name, as_no_tracking=True
            )

            # Mapping basket entity to ShoppingCartDto
            items_dto = [
                ShoppingCartItemDto(
                    id=item.id,
                    shopping_cart_id=item.shopping_cart_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    color=item.color,
                    price=item.price,
                    product_name=item.product_name,
                )
                for item in basket.items
            ]

            basket_dto = ShoppingCartDto(
                id=basket.id,
                user_name=basket.user_name,
                items=items_dto,
            )
        except BasketNotFoundException:
            # Return an empty basket if it doesn't exist yet
            # The basket will be created automatically when the first item is added
            basket_dto = ShoppingCartDto(
                id=None,  # No ID yet - basket will be created when first item is added
                user_name=query.user_name,
                items=[],
            )

        return GetBasketResult(shopping_cart=basket_dto)
