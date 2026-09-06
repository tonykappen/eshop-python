"""GetOrdersHandler with 1-1 parity to .NET implementation."""

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.core.pagination.models import PaginatedResult
from app.modules.ordering.application.mappers.order_mapper import OrderMapper
from app.modules.ordering.domain.repositories.order import IOrderRepository

from .get_orders_query import GetOrdersQuery, GetOrdersResult


class GetOrdersHandler(IRequestHandler[GetOrdersQuery, GetOrdersResult]):
    """Handler for GetOrdersQuery - matches .NET GetOrdersHandler."""

    def __init__(self, repository: IOrderRepository) -> None:
        """
        Initialize handler.

        Args:
            repository: Order repository
        """
        self.repository = repository

    async def handle(
        self, query: GetOrdersQuery, cancellation_token: CancellationToken
    ) -> GetOrdersResult:
        """
        Handle the query - matches .NET Handle(GetOrdersQuery query, CancellationToken cancellationToken).

        Uses patterns matching .NET:
        - LongCountAsync() for total count
        - AsNoTracking() for read operations
        - Include(x => x.Items) for eager loading
        - OrderBy(p => p.OrderName) for ordering
        - Skip() and Take() for pagination

        Args:
            query: The query to handle
            cancellation_token: Cancellation token

        Returns:
            GetOrdersResult containing paginated orders
        """
        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        page_index = query.pagination_request.page_index
        page_size = query.pagination_request.page_size

        # Get orders with pagination using real database session (no mocking)
        # Repository should use AsNoTracking(), Include(), OrderBy(), Skip(), Take()
        orders, total_count = await self.repository.get_all(
            skip=page_size * page_index, take=page_size
        )

        # Map orders to DTOs (matching .NET Adapt<List<OrderDto>> pattern)
        order_dtos = [OrderMapper.to_dto(order) for order in orders]

        # Create paginated result matching .NET PaginatedResult structure
        paginated_result = PaginatedResult.create(
            items=order_dtos,
            total=total_count,
            page=page_index + 1,  # Convert 0-based to 1-based for display
            size=page_size,
        )

        return GetOrdersResult(orders=paginated_result)
