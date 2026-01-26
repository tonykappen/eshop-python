"""Handler registration for ordering module."""

import asyncio
import logging

from app.core.mediator.handler_registry import HandlerRegistry
from app.modules.ordering.infrastructure.persistence.db_context import get_session_maker
from app.modules.ordering.infrastructure.persistence.repositories.orders.sql_order_repository import (
    SqlOrderRepository,
)

logger = logging.getLogger(__name__)


def register_ordering_handlers(handler_registry: HandlerRegistry) -> None:
    """
    Register all ordering handlers with the handler registry.

    Creates handler instances with their dependencies (repositories).
    Handlers are created with repositories that use a session from the session maker.
    Note: For production use, consider using a factory pattern that resolves
    dependencies per-request via FastAPI DI.

    Args:
        handler_registry: Handler registry to register handlers with
    """
    from app.modules.ordering.application.features.orders.command.create_order.create_order_handler import (
        CreateOrderHandler,
    )
    from app.modules.ordering.application.features.orders.command.delete_order.delete_order_handler import (
        DeleteOrderHandler,
    )
    from app.modules.ordering.application.features.orders.query.get_order_by_id.get_order_by_id_handler import (
        GetOrderByIdHandler,
    )
    from app.modules.ordering.application.features.orders.query.get_orders.get_orders_handler import (
        GetOrdersHandler,
    )
    from app.modules.ordering.application.features.orders.command.create_order.create_order_command import (
        CreateOrderCommand,
    )
    from app.modules.ordering.application.features.orders.command.delete_order.delete_order_command import (
        DeleteOrderCommand,
    )
    from app.modules.ordering.application.features.orders.query.get_order_by_id.get_order_by_id_query import (
        GetOrderByIdQuery,
    )
    from app.modules.ordering.application.features.orders.query.get_orders.get_orders_query import (
        GetOrdersQuery,
    )

    # Create repository instances for handlers
    # We create a temporary session for registration purposes
    # In production, handlers should ideally get new sessions per-request via FastAPI DI
    session_maker = get_session_maker()

    async def create_handlers_with_dependencies():
        """Create handler instances with dependencies."""
        # Create a session for repository creation
        async with session_maker() as session:
            # Create repository instance
            repository = SqlOrderRepository(session)

            # Create handler instances with the repository
            get_orders_handler = GetOrdersHandler(repository)
            get_order_by_id_handler = GetOrderByIdHandler(repository)
            create_order_handler = CreateOrderHandler(repository)
            delete_order_handler = DeleteOrderHandler(repository)

            # Register handlers
            handler_registry.register_handler(GetOrdersQuery, get_orders_handler)
            handler_registry.register_handler(
                GetOrderByIdQuery, get_order_by_id_handler
            )
            handler_registry.register_handler(CreateOrderCommand, create_order_handler)
            handler_registry.register_handler(DeleteOrderCommand, delete_order_handler)

            logger.info("Registered ordering handlers with dependencies")

    # Run the async function to create handlers
    # Handle different event loop scenarios
    try:
        # Try to get the current event loop
        asyncio.get_running_loop()
        # If we're in an async context, create a new event loop in a thread
        logger.info("Event loop is already running. Creating handlers in separate thread.")
        import threading

        def run_in_new_loop():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                new_loop.run_until_complete(create_handlers_with_dependencies())
            finally:
                new_loop.close()

        thread = threading.Thread(target=run_in_new_loop, daemon=False)
        thread.start()
        thread.join(timeout=10)  # Wait up to 10 seconds
        if thread.is_alive():
            raise RuntimeError("Handler registration timed out")
    except RuntimeError:
        # No event loop running, create one
        asyncio.run(create_handlers_with_dependencies())
