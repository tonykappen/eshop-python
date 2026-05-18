"""SQL implementation of IOrderRepository - matches .NET patterns exactly."""

import logging
from uuid import UUID

from app.modules.ordering.domain.entities.order.order import Order, OrderItem
from app.modules.ordering.domain.exceptions.order import OrderNotFoundException
from app.modules.ordering.domain.repositories.order import IOrderRepository
from app.modules.ordering.domain.value_objects import Address, Payment
from app.modules.ordering.infrastructure.persistence.orm.orders.order_item_orm import \
    OrderItemORM
from app.modules.ordering.infrastructure.persistence.orm.orders.order_orm import \
    OrderORM
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class SqlOrderRepository(IOrderRepository):
    """
    SQL implementation of IOrderRepository - matches .NET OrderRepository patterns.

    Uses real database sessions (no mocking logic in code).
    Query patterns match .NET:
    - AsNoTracking() for read operations
    - Include() for eager loading
    - SingleOrDefaultAsync() / FindAsync() patterns
    - OrderBy(), Skip(), Take() for pagination
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Real database session (no mocking)
        """
        self.session = session

    async def add(self, order: Order) -> None:
        """
        Add a new order - matches .NET dbContext.Orders.Add(order).

        Args:
            order: Order to add
        """
        order_orm = self._domain_to_orm(order)
        self.session.add(order_orm)

    async def get_by_id(self, order_id: UUID) -> Order | None:
        """
        Get an order by ID - matches .NET SingleOrDefaultAsync with Include.

        Uses AsNoTracking() and Include(x => x.Items) patterns.

        Args:
            order_id: Order ID

        Returns:
            Order if found, None otherwise
        """
        # Use AsNoTracking() for read operations (matching .NET)
        stmt = (
            select(OrderORM)
            .where(OrderORM.id == order_id)
            .options(selectinload(OrderORM.items))  # Include(x => x.Items)
            .execution_options(populate_existing=True)  # AsNoTracking equivalent
        )

        result = await self.session.execute(stmt)
        order_orm = result.scalar_one_or_none()  # SingleOrDefaultAsync pattern

        if order_orm is None:
            return None

        return self._orm_to_domain(order_orm)

    async def get_all(self, skip: int = 0, take: int = 10) -> tuple[list[Order], int]:
        """
        Get all orders with pagination - matches .NET GetOrdersHandler patterns.

        Uses:
        - LongCountAsync() for total count
        - AsNoTracking() for read operations
        - Include(x => x.Items) for eager loading
        - OrderBy(p => p.OrderName) for ordering
        - Skip() and Take() for pagination

        Args:
            skip: Number of orders to skip
            take: Number of orders to take

        Returns:
            Tuple of (list of orders, total count)
        """
        # Get total count - matching .NET LongCountAsync()
        count_stmt = select(func.count(OrderORM.id))
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalar_one()

        # Get paginated orders - matching .NET patterns
        stmt = (
            select(OrderORM)
            .options(selectinload(OrderORM.items))  # Include(x => x.Items)
            .order_by(OrderORM.order_name)  # OrderBy(p => p.OrderName)
            .offset(skip)  # Skip()
            .limit(take)  # Take()
            .execution_options(populate_existing=True)  # AsNoTracking equivalent
        )

        result = await self.session.execute(stmt)
        orders_orm = result.scalars().all()

        orders = [self._orm_to_domain(order_orm) for order_orm in orders_orm]

        return orders, total_count

    async def remove(self, order: Order) -> None:
        """
        Remove an order - matches .NET dbContext.Orders.Remove(order).

        Args:
            order: Order to remove
        """
        # Find order ORM - matching .NET FindAsync() pattern
        order_orm = await self.session.get(OrderORM, order.id)

        if order_orm is None:
            raise OrderNotFoundException(order.id)

        await self.session.delete(order_orm)

    async def save_changes_async(self) -> None:
        """
        Save changes to the database - matches .NET SaveChangesAsync.

        This method commits all tracked changes, matching .NET Entity Framework behavior.
        """
        try:
            await self.session.flush()
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error saving changes: {e}")
            await self.session.rollback()
            raise

    def _orm_to_domain(self, order_orm: OrderORM) -> Order:
        """
        Convert ORM model to domain model.

        Args:
            order_orm: Order ORM model

        Returns:
            Order domain model
        """
        # Reconstruct Address value objects from embedded columns
        # Use Address.of() to match .NET pattern, but handle optional fields
        shipping_address = Address(
            first_name=order_orm.shipping_address_first_name,
            last_name=order_orm.shipping_address_last_name,
            email_address=order_orm.shipping_address_email_address or "",
            address_line=order_orm.shipping_address_address_line,
            country=order_orm.shipping_address_country or "",
            state=order_orm.shipping_address_state or "",
            zip_code=order_orm.shipping_address_zip_code,
        )

        billing_address = Address(
            first_name=order_orm.billing_address_first_name,
            last_name=order_orm.billing_address_last_name,
            email_address=order_orm.billing_address_email_address or "",
            address_line=order_orm.billing_address_address_line,
            country=order_orm.billing_address_country or "",
            state=order_orm.billing_address_state or "",
            zip_code=order_orm.billing_address_zip_code,
        )

        # Reconstruct Payment value object from embedded columns
        # Direct construction (not .of()) to handle optional card_name from ORM
        payment = Payment(
            card_name=order_orm.payment_card_name,
            card_number=order_orm.payment_card_number,
            expiration=order_orm.payment_expiration or "",
            cvv=order_orm.payment_cvv or "",
            payment_method=order_orm.payment_payment_method,
        )

        # Convert items
        items = []
        for item_orm in order_orm.items or []:
            item = OrderItem(
                order_id=item_orm.order_id,
                product_id=item_orm.product_id,
                quantity=item_orm.quantity,
                price=item_orm.price,
                id=item_orm.id,
            )
            items.append(item)

        # Create domain model
        order = Order(
            id=order_orm.id,
            customer_id=order_orm.customer_id,
            order_name=order_orm.order_name,
            shipping_address=shipping_address,
            billing_address=billing_address,
            payment=payment,
            items=items,
            version=order_orm.version,
            created_at=order_orm.created_at,
            last_modified=order_orm.updated_at,
        )

        return order

    def _domain_to_orm(self, order: Order) -> OrderORM:
        """
        Convert domain model to ORM model.

        Args:
            order: Order domain model

        Returns:
            Order ORM model
        """
        # Create order ORM with embedded Address and Payment columns
        order_orm = OrderORM(
            id=order.id,
            customer_id=order.customer_id,
            order_name=order.order_name,
            # Shipping Address - embedded columns
            shipping_address_first_name=order.shipping_address.first_name,
            shipping_address_last_name=order.shipping_address.last_name,
            shipping_address_email_address=order.shipping_address.email_address,
            shipping_address_address_line=order.shipping_address.address_line,
            shipping_address_country=order.shipping_address.country,
            shipping_address_state=order.shipping_address.state,
            shipping_address_zip_code=order.shipping_address.zip_code,
            # Billing Address - embedded columns
            billing_address_first_name=order.billing_address.first_name,
            billing_address_last_name=order.billing_address.last_name,
            billing_address_email_address=order.billing_address.email_address,
            billing_address_address_line=order.billing_address.address_line,
            billing_address_country=order.billing_address.country,
            billing_address_state=order.billing_address.state,
            billing_address_zip_code=order.billing_address.zip_code,
            # Payment - embedded columns
            payment_card_name=order.payment.card_name,
            payment_card_number=order.payment.card_number,
            payment_expiration=order.payment.expiration,
            payment_cvv=order.payment.cvv,
            payment_payment_method=order.payment.payment_method,
            version=order.version,
            created_at=order.created_at,
            updated_at=order.last_modified or order.created_at,
        )

        # Create items ORM
        items_orm = []
        for item in order.items:
            item_orm = OrderItemORM(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price,
                created_at=order.created_at,
                updated_at=order.last_modified or order.created_at,
            )
            items_orm.append(item_orm)

        order_orm.items = items_orm
        return order_orm
