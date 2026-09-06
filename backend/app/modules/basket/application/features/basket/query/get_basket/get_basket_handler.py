"""GetBasketHandler with 1-1 parity to .NET implementation."""

from collections.abc import Callable
from typing import Any

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.basket.application.basket_handler_context import use_basket_context
from app.modules.basket.application.dtos.shopping_cart_dto import (
    ShoppingCartDto, ShoppingCartItemDto)
from app.modules.basket.domain.repositories.basket import IBasketRepository

from .get_basket_query import GetBasketQuery, GetBasketResult


class GetBasketHandler(IRequestHandler[GetBasketQuery, GetBasketResult]):
    """Handler for GetBasketQuery - matches .NET GetBasketHandler."""

    def __init__(
        self,
        repository: IBasketRepository | None = None,
        context_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._repository = repository
        self._context_factory = context_factory

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
        cancellation_token.throw_if_cancellation_requested()

        async with use_basket_context(
            self._context_factory, repository=self._repository
        ) as ctx:
            return await self._handle_with_repository(query, ctx.repository)

    async def _handle_with_repository(
        self, query: GetBasketQuery, repository: IBasketRepository
    ) -> GetBasketResult:
        from app.modules.basket.domain.exceptions.basket.basket_not_found import \
            BasketNotFoundException

        try:
            basket = await repository.get_basket(query.user_name, as_no_tracking=True)

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
            basket_dto = ShoppingCartDto(
                id=None,
                user_name=query.user_name,
                items=[],
            )

        return GetBasketResult(shopping_cart=basket_dto)
