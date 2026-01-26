"""GetOrderByIdHandler with 1-1 parity to .NET implementation."""

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.ordering.domain.exceptions.order import OrderNotFoundException
from app.modules.ordering.domain.repositories.order import IOrderRepository

from .get_order_by_id_query import GetOrderByIdQuery, GetOrderByIdResult


class GetOrderByIdHandler(IRequestHandler[GetOrderByIdQuery, GetOrderByIdResult]):
    """Handler for GetOrderByIdQuery - matches .NET GetOrderByIdHandler."""

    def __init__(self, repository: IOrderRepository) -> None:
        """
        Initialize handler.

        Args:
            repository: Order repository
        """
        self.repository = repository

    async def handle(
        self, query: GetOrderByIdQuery, cancellation_token: CancellationToken
    ) -> GetOrderByIdResult:
        """
        Handle the query - matches .NET Handle(GetOrderByIdQuery query, CancellationToken cancellationToken).

        Uses AsNoTracking() and Include() patterns matching .NET:
        - AsNoTracking() for read operations
        - Include(x => x.Items) for eager loading

        Args:
            query: The query to handle
            cancellation_token: Cancellation token

        Returns:
            GetOrderByIdResult containing the order

        Raises:
            OrderNotFoundException: If order is not found
        """
        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Get order using SingleOrDefaultAsync pattern with Include (matching .NET)
        # Repository should use AsNoTracking() and Include() internally
        order = await self.repository.get_by_id(query.id)

        if order is None:
            raise OrderNotFoundException(query.id)

        # Map order to DTO (matching .NET Adapt<OrderDto> pattern)
        from app.modules.ordering.application.mappers.order_mapper import (
            OrderMapper,
        )

        order_dto = OrderMapper.to_dto(order)

        return GetOrderByIdResult(order=order_dto)
