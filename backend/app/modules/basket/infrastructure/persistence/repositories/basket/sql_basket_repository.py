"""SQL implementation of IBasketRepository."""

import inspect
import logging
from decimal import Decimal
from uuid import UUID

from app.modules.basket.domain.entities.basket import (ShoppingCart,
                                                       ShoppingCartItem)
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException
from app.modules.basket.domain.repositories.basket import IBasketRepository
from app.modules.basket.infrastructure.persistence.orm.basket.shopping_cart_item_orm import \
    ShoppingCartItemORM
from app.modules.basket.infrastructure.persistence.orm.basket.shopping_cart_orm import \
    ShoppingCartORM
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


async def _extract_value(value, depth=0, max_depth=3):
    """
    Extract actual value from potentially awaitable objects.

    In production, ORM objects should return real values, not mocks.
    This function handles edge cases where values might be coroutines.

    Args:
        value: Value that might be a coroutine or actual value
        depth: Current recursion depth
        max_depth: Maximum recursion depth to prevent infinite loops

    Returns:
        Actual value
    """
    # Prevent infinite recursion
    if depth >= max_depth:
        logger.error(
            f"Maximum recursion depth ({max_depth}) reached - this should not happen in production!"
        )
        return value

    # Handle None
    if value is None:
        return None

    # Check if it's a coroutine or awaitable
    if inspect.iscoroutine(value):
        try:
            value = await value
            # After awaiting, check if result is also awaitable (limit recursion)
            if depth < max_depth - 1 and (
                inspect.iscoroutine(value) or hasattr(value, "__await__")
            ):
                return await _extract_value(value, depth + 1, max_depth)
            return value
        except Exception as e:
            logger.error(f"Error awaiting coroutine: {e}")
            return value

    # Check if it has __await__ method (other awaitable types)
    if hasattr(value, "__await__"):
        try:
            # Try to get the iterator and get the first value
            await_iter = value.__await__()
            if hasattr(await_iter, "__next__"):
                try:
                    value = await_iter.__next__()
                    if depth < max_depth - 1:
                        return await _extract_value(value, depth + 1, max_depth)
                    return value
                except StopIteration as e:
                    # If StopIteration has a value, use it
                    return e.value if hasattr(e, "value") else value
        except Exception as e:
            logger.error(f"Error extracting from awaitable: {e}")
            return value

    # Check if it's a mock object - this should NEVER happen in production
    # If we detect a mock, fail immediately with a clear error
    is_mock = (
        hasattr(value, "_mock_name")
        or hasattr(value, "_spec_class")
        or (hasattr(value, "__class__") and "Mock" in str(value.__class__.__name__))
    )

    if is_mock:
        error_msg = (
            f"CRITICAL: Mock object detected in production code! Type: {type(value)}. "
            f"Only real database sessions are allowed. "
            f"Check that get_basket_session() returns a real AsyncSession, not a mock."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # It's a regular value, return it
    return value


class SqlBasketRepository(IBasketRepository):
    """SQL implementation of IBasketRepository - matches .NET BasketRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.

        Args:
            session: Database session
        """
        # Validate that we're using a real session, not a mock
        session_is_mock = (
            hasattr(session, "_mock_name")
            or hasattr(session, "_spec_class")
            or (
                hasattr(session, "__class__")
                and "Mock" in str(session.__class__.__name__)
            )
        )
        if session_is_mock:
            error_msg = (
                f"CRITICAL: Mock session detected in SqlBasketRepository! Type: {type(session)}. "
                f"This should not happen in production. Only real database sessions are allowed."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.session = session

    async def get_basket(
        self, user_name: str, as_no_tracking: bool = True
    ) -> ShoppingCart:
        """
        Get basket by user name - matches .NET GetBasket method.

        When as_no_tracking=False, the ORM object is tracked and changes can be persisted
        via SaveChangesAsync (matching .NET Entity Framework behavior).

        Args:
            user_name: User name
            as_no_tracking: Whether to use no-tracking mode (default: True)
                           When False, ORM is tracked and domain changes should be synced via update_basket

        Returns:
            ShoppingCart instance

        Raises:
            BasketNotFoundException: If basket not found
        """
        # Validate session is not a mock BEFORE executing query
        session_is_mock = (
            hasattr(self.session, "_mock_name")
            or hasattr(self.session, "_spec_class")
            or (
                hasattr(self.session, "__class__")
                and "Mock" in str(self.session.__class__.__name__)
            )
        )
        if session_is_mock:
            error_msg = (
                f"CRITICAL: Database session is a mock object! Type: {type(self.session)}. "
                f"This should not happen in production. "
                f"Check that get_basket_session() dependency returns a real AsyncSession, not a mock."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            stmt = (
                select(ShoppingCartORM)
                .where(ShoppingCartORM.user_name == user_name)
                .options(selectinload(ShoppingCartORM.items))
            )

            # When as_no_tracking=False, don't use populate_existing to keep object tracked
            # This matches .NET Entity Framework behavior where tracked entities can be modified
            if as_no_tracking:
                stmt = stmt.execution_options(populate_existing=True)

            result = await self.session.execute(stmt)
            basket_orm = result.scalar_one_or_none()

            if basket_orm is None:
                raise BasketNotFoundException(user_name)

            # Validate that we got a real ORM object, not a mock
            is_mock = (
                hasattr(basket_orm, "_mock_name")
                or hasattr(basket_orm, "_spec_class")
                or (
                    hasattr(basket_orm, "__class__")
                    and "Mock" in str(basket_orm.__class__.__name__)
                )
            )
            if is_mock:
                error_msg = (
                    "CRITICAL: Database query returned a mock object! "
                    "This means the session is a mock. "
                    "Check that get_basket_session() returns a real AsyncSession."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Store ORM reference for tracking when as_no_tracking=False
            # This allows us to sync domain changes back to ORM later
            domain_basket = await self._orm_to_domain(basket_orm)
            if not as_no_tracking:
                # Store the ORM object reference so we can update it later
                # This matches .NET behavior where tracked entities can be modified
                if not hasattr(self, "_tracked_baskets"):
                    self._tracked_baskets = {}
                self._tracked_baskets[domain_basket.id] = basket_orm

            return domain_basket

        except BasketNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting basket for user {user_name}: {e}")
            raise

    async def create_basket(self, basket: ShoppingCart) -> ShoppingCart:
        """
        Create a new basket - matches .NET CreateBasket method.

        Args:
            basket: ShoppingCart to create (may include items)

        Returns:
            Created ShoppingCart instance
        """
        try:
            basket_orm = self._domain_to_orm(basket)
            self.session.add(basket_orm)
            await self.session.flush()

            # Reload the basket with relationships to avoid lazy loading issues in async mode
            # After flush, we need to query again with selectinload to ensure items are loaded
            # This ensures the object is properly attached and relationships are eagerly loaded
            # Use the ORM object's ID directly to ensure we get the same object from the session
            basket_orm_loaded = await self.session.get(ShoppingCartORM, basket_orm.id)

            # If not in identity map, query for it
            if not basket_orm_loaded:
                stmt = (
                    select(ShoppingCartORM)
                    .where(ShoppingCartORM.id == basket_orm.id)
                    .options(selectinload(ShoppingCartORM.items))
                )
                result = await self.session.execute(stmt)
                basket_orm_loaded = result.scalar_one()

            # Ensure we have the actual ORM object, not a coroutine
            if inspect.iscoroutine(basket_orm_loaded):
                basket_orm_loaded = await basket_orm_loaded

            # Validate that we got a real ORM object, not a mock
            is_mock = (
                hasattr(basket_orm_loaded, "_mock_name")
                or hasattr(basket_orm_loaded, "_spec_class")
                or (
                    hasattr(basket_orm_loaded, "__class__")
                    and "Mock" in str(basket_orm_loaded.__class__.__name__)
                )
            )
            if is_mock:
                error_msg = (
                    "CRITICAL: Database query returned a mock object in create_basket! "
                    "This means the session is a mock. "
                    "Check that get_basket_session() returns a real AsyncSession."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Convert to domain model
            domain_basket = await self._orm_to_domain(basket_orm_loaded)

            # Store the ORM object in tracked cache so it can be updated later if needed
            # This matches .NET behavior where created entities are tracked
            if not hasattr(self, "_tracked_baskets"):
                self._tracked_baskets = {}
            self._tracked_baskets[domain_basket.id] = basket_orm_loaded

            return domain_basket

        except Exception as e:
            logger.error(f"Error creating basket: {e}")
            raise

    async def add_items_to_basket(self, basket: ShoppingCart) -> ShoppingCart:
        """
        Add items to an existing basket ORM object.
        This is used when a basket was just created and items need to be added.

        Args:
            basket: ShoppingCart domain model with items to add

        Returns:
            Updated ShoppingCart instance
        """
        try:
            # For newly created baskets, query by ID first (most reliable)
            stmt = (
                select(ShoppingCartORM)
                .where(ShoppingCartORM.id == basket.id)
                .options(selectinload(ShoppingCartORM.items))
            )
            result = await self.session.execute(stmt)
            basket_orm = result.scalar_one_or_none()

            # If not found by ID, try by user_name (fallback)
            if not basket_orm:
                logger.warning(
                    f"Basket not found by ID {basket.id}, trying by user_name {basket.user_name}"
                )
                stmt_by_user = (
                    select(ShoppingCartORM)
                    .where(ShoppingCartORM.user_name == basket.user_name)
                    .options(selectinload(ShoppingCartORM.items))
                )
                result_by_user = await self.session.execute(stmt_by_user)
                basket_orm = result_by_user.scalar_one_or_none()

            # If still not found, this is an error
            if not basket_orm:
                logger.error(
                    f"Basket not found for adding items: id={basket.id}, user_name={basket.user_name}. "
                    f"Session state: {len(list(self.session.identity_map.values()))} objects in identity map"
                )
                from app.modules.basket.domain.exceptions.basket.basket_not_found import \
                    BasketNotFoundException

                raise BasketNotFoundException(basket.user_name)

            # Ensure items are loaded
            if not hasattr(basket_orm, "items") or basket_orm.items is None:
                await self.session.refresh(basket_orm, ["items"])

            # Add new items that aren't already in the ORM
            existing_item_ids = {item.id for item in (basket_orm.items or [])}
            for item in basket.items:
                if item.id not in existing_item_ids:
                    from datetime import datetime

                    item_orm = ShoppingCartItemORM(
                        id=item.id,
                        shopping_cart_id=item.shopping_cart_id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        color=item.color,
                        price=item.price,
                        product_name=item.product_name,
                        created_at=basket.created_at or datetime.utcnow(),
                        updated_at=basket.last_modified
                        or basket.created_at
                        or datetime.utcnow(),
                    )
                    basket_orm.items.append(item_orm)
                    self.session.add(item_orm)

            # Update basket metadata
            from datetime import datetime

            basket_orm.version = basket.version
            basket_orm.updated_at = basket.last_modified or datetime.utcnow()

            await self.session.flush()

            # Reload to get updated relationships
            await self.session.refresh(basket_orm)
            stmt_reload = (
                select(ShoppingCartORM)
                .where(ShoppingCartORM.id == basket_orm.id)
                .options(selectinload(ShoppingCartORM.items))
            )
            result_reload = await self.session.execute(stmt_reload)
            basket_orm_loaded = result_reload.scalar_one()

            return await self._orm_to_domain(basket_orm_loaded)

        except Exception as e:
            logger.error(f"Error adding items to basket: {e}")
            raise

    async def delete_basket(self, user_name: str) -> bool:
        """
        Delete basket by user name - matches .NET DeleteBasket method.

        Note: In .NET, this calls SaveChangesAsync which commits.
        In Python, we mark for deletion and let save_changes_async commit.

        Args:
            user_name: User name

        Returns:
            True if deleted successfully

        Raises:
            BasketNotFoundException: If basket not found
        """
        try:
            # Get basket first (will raise BasketNotFoundException if not found)
            basket = await self.get_basket(user_name, as_no_tracking=False)

            # Get the ORM object - try from tracked cache first
            basket_orm = None
            if hasattr(self, "_tracked_baskets") and basket.id in self._tracked_baskets:
                basket_orm = self._tracked_baskets[basket.id]
            else:
                # Query for it
                basket_orm = await self.session.get(ShoppingCartORM, basket.id)

            if not basket_orm:
                # Fallback: query by user_name
                stmt = select(ShoppingCartORM).where(
                    ShoppingCartORM.user_name == user_name
                )
                result = await self.session.execute(stmt)
                basket_orm = result.scalar_one_or_none()

            if basket_orm:
                # Mark for deletion (cascade will delete items)
                await self.session.delete(basket_orm)
                # Don't flush here - let save_changes_async commit everything together
                # This matches .NET behavior where SaveChangesAsync commits

            return True

        except BasketNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting basket for user {user_name}: {e}")
            raise

    async def update_basket(self, basket: ShoppingCart) -> ShoppingCart:
        """
        Update an existing basket with its items - matches .NET SaveChangesAsync behavior.

        This method updates the ORM objects based on the domain entity changes.
        It syncs domain model changes to the tracked ORM object, matching .NET Entity Framework behavior.

        Args:
            basket: ShoppingCart domain model with updated items

        Returns:
            Updated ShoppingCart instance
        """
        try:
            # First, try to get the tracked ORM object if we stored it
            basket_orm = None
            if hasattr(self, "_tracked_baskets") and basket.id in self._tracked_baskets:
                basket_orm = self._tracked_baskets[basket.id]
                # Refresh to ensure we have latest state
                await self.session.refresh(basket_orm, ["items"])

            # If not in tracked cache, query for it
            if not basket_orm:
                stmt = (
                    select(ShoppingCartORM)
                    .where(ShoppingCartORM.id == basket.id)
                    .options(selectinload(ShoppingCartORM.items))
                )
                result = await self.session.execute(stmt)
                basket_orm = result.scalar_one_or_none()

            # If still not found, try by user_name as fallback
            if not basket_orm:
                stmt_by_user = (
                    select(ShoppingCartORM)
                    .where(ShoppingCartORM.user_name == basket.user_name)
                    .options(selectinload(ShoppingCartORM.items))
                )
                result_by_user = await self.session.execute(stmt_by_user)
                basket_orm = result_by_user.scalar_one_or_none()

                if not basket_orm:
                    logger.error(
                        f"Basket not found for update: id={basket.id}, user_name={basket.user_name}"
                    )
                    from app.modules.basket.domain.exceptions.basket.basket_not_found import \
                        BasketNotFoundException

                    raise BasketNotFoundException(basket.user_name)

            # Update basket fields
            from datetime import datetime

            basket_orm.user_name = basket.user_name
            basket_orm.version = basket.version
            basket_orm.updated_at = basket.last_modified or datetime.utcnow()

            # Get existing items from ORM
            existing_items = {item.id: item for item in basket_orm.items}

            # Update or add items
            for item in basket.items:
                if item.id in existing_items:
                    # Update existing item
                    item_orm = existing_items[item.id]
                    item_orm.quantity = item.quantity
                    item_orm.color = item.color
                    item_orm.price = item.price
                    item_orm.product_name = item.product_name
                    item_orm.updated_at = basket.last_modified or item_orm.updated_at
                else:
                    # Add new item
                    item_orm = ShoppingCartItemORM(
                        id=item.id,
                        shopping_cart_id=item.shopping_cart_id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        color=item.color,
                        price=item.price,
                        product_name=item.product_name,
                        created_at=basket.created_at,
                        updated_at=basket.last_modified or basket.created_at,
                    )
                    basket_orm.items.append(item_orm)
                    self.session.add(item_orm)

            # Remove items that are no longer in the domain entity
            domain_item_ids = {item.id for item in basket.items}
            items_to_remove = [
                item for item in basket_orm.items if item.id not in domain_item_ids
            ]
            for item_orm in items_to_remove:
                await self.session.delete(item_orm)
                basket_orm.items.remove(item_orm)

            await self.session.flush()

            # Reload to get updated relationships
            await self.session.refresh(basket_orm)
            stmt = (
                select(ShoppingCartORM)
                .where(ShoppingCartORM.id == basket_orm.id)
                .options(selectinload(ShoppingCartORM.items))
            )
            result = await self.session.execute(stmt)
            basket_orm_loaded = result.scalar_one()

            return await self._orm_to_domain(basket_orm_loaded)

        except Exception as e:
            logger.error(f"Error updating basket: {e}")
            raise

    async def save_changes_async(self, user_name: str | None = None) -> int:
        """
        Save changes to the database - matches .NET SaveChangesAsync method.

        This method commits all tracked changes in the session, matching .NET Entity Framework behavior.
        In .NET, SaveChangesAsync commits the transaction, so we do the same here.

        Args:
            user_name: Optional user name for audit purposes

        Returns:
            Number of affected rows
        """
        try:
            # Count changes before flush/commit (matching .NET behavior)
            change_count = (
                len(self.session.new)
                + len(self.session.dirty)
                + len(self.session.deleted)
            )

            # Flush all pending changes first (sends SQL to database)
            await self.session.flush()

            # Commit the transaction - matches .NET SaveChangesAsync which commits
            # This ensures changes are persisted immediately, not just staged
            await self.session.commit()

            return (
                change_count if change_count > 0 else 1
            )  # Return at least 1 to indicate success

        except Exception as e:
            logger.error(f"Error saving changes: {e}")
            # Rollback on error
            await self.session.rollback()
            raise

    async def update_items_price(self, product_id: UUID, new_price: Decimal) -> bool:
        """
        Update price for all items with given product_id - used by UpdateItemPriceInBasketHandler.

        Args:
            product_id: Product ID to update
            new_price: New price

        Returns:
            True if any items were updated, False otherwise
        """
        try:
            stmt = (
                update(ShoppingCartItemORM)
                .where(ShoppingCartItemORM.product_id == product_id)
                .values(price=new_price)
            )
            result = await self.session.execute(stmt)
            await self.session.flush()

            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating items price for product {product_id}: {e}")
            raise

    async def _orm_to_domain(self, basket_orm: ShoppingCartORM) -> ShoppingCart:
        """
        Convert ORM model to domain model.

        Args:
            basket_orm: ShoppingCart ORM model (may be a coroutine in async mode)

        Returns:
            ShoppingCart domain model
        """
        # Validate that basket_orm is a real ORM object, not a mock
        is_orm_mock = (
            hasattr(basket_orm, "_mock_name")
            or hasattr(basket_orm, "_spec_class")
            or (
                hasattr(basket_orm, "__class__")
                and "Mock" in str(basket_orm.__class__.__name__)
            )
        )

        if is_orm_mock:
            error_msg = (
                f"CRITICAL: basket_orm is a mock object! Type: {type(basket_orm)}. "
                f"This means the database session is returning mock objects. "
                f"Only real database sessions are allowed. Check that get_basket_session() returns a real AsyncSession."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Handle case where basket_orm itself might be a coroutine or awaitable
        # Try to access an attribute - if it fails, it might be a coroutine
        try:
            test_id = basket_orm.id  # Try to access an attribute
            # If it's a mock or coroutine, await it
            if inspect.iscoroutine(test_id) or hasattr(test_id, "__await__"):
                if inspect.iscoroutine(basket_orm) or hasattr(basket_orm, "__await__"):
                    basket_orm = await basket_orm
        except (AttributeError, TypeError):
            # If accessing attributes fails, it might be a coroutine - await it
            if inspect.iscoroutine(basket_orm) or hasattr(basket_orm, "__await__"):
                basket_orm = await basket_orm

        # Extract actual values from ORM object
        # Always extract to handle edge cases with coroutines/mocks
        try:
            # Get raw values first
            basket_id_raw = basket_orm.id
            user_name_raw = basket_orm.user_name
            version_raw = basket_orm.version
            created_at_raw = basket_orm.created_at
            updated_at_raw = basket_orm.updated_at

            # Always extract to ensure we get real values (handles coroutines and mocks)
            basket_id = await _extract_value(basket_id_raw)
            user_name = await _extract_value(user_name_raw)
            version = await _extract_value(version_raw)
            created_at = await _extract_value(created_at_raw)
            updated_at = await _extract_value(updated_at_raw)

            # Validate that we got real values (extraction should handle coroutines)
            if basket_id is None or user_name is None:
                error_msg = (
                    f"Could not extract values from ORM attributes! "
                    f"basket_id: {basket_id}, user_name: {user_name}. "
                    f"This suggests an issue with the ORM object or database session."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

        except ValueError:
            # Re-raise ValueError (our custom error)
            raise
        except Exception as e:
            logger.error(f"Error extracting basket attributes: {e}", exc_info=True)
            raise

        # Handle items relationship - it might be a coroutine in async mode
        try:
            items_orm = basket_orm.items
            # Check if items is a coroutine
            if inspect.iscoroutine(items_orm) or hasattr(items_orm, "__await__"):
                items_orm = await items_orm
        except AttributeError:
            # If items doesn't exist, use empty list
            items_orm = []

        # Ensure items_orm is iterable (list, tuple, etc.)
        if items_orm is None:
            items_orm = []
        elif not hasattr(items_orm, "__iter__"):
            logger.warning(
                f"Unexpected items type: {type(items_orm)}, converting to list"
            )
            items_orm = list(items_orm) if items_orm else []

        # Convert items - always extract to ensure real values
        items = []
        for item_orm in items_orm:
            # Always extract values to handle coroutines/mocks
            item_id = await _extract_value(item_orm.id)
            item_cart_id = await _extract_value(item_orm.shopping_cart_id)
            item_product_id = await _extract_value(item_orm.product_id)
            item_quantity = await _extract_value(item_orm.quantity)
            item_color = await _extract_value(item_orm.color)
            item_price = await _extract_value(item_orm.price)
            item_product_name = await _extract_value(item_orm.product_name)

            item = ShoppingCartItem(
                id=item_id,
                shopping_cart_id=item_cart_id,
                product_id=item_product_id,
                quantity=item_quantity,
                color=item_color,
                price=item_price,
                product_name=item_product_name,
            )
            items.append(item)

        # Create domain model with extracted values
        basket = ShoppingCart(
            id=basket_id,
            user_name=user_name,
            items=items,
            version=version,
            created_at=created_at,
            last_modified=updated_at,
        )

        return basket

    def _domain_to_orm(self, basket: ShoppingCart) -> ShoppingCartORM:
        """
        Convert domain model to ORM model.

        Args:
            basket: ShoppingCart domain model

        Returns:
            ShoppingCart ORM model
        """
        # Create basket ORM
        basket_orm = ShoppingCartORM(
            id=basket.id,
            user_name=basket.user_name,
            version=basket.version,
            created_at=basket.created_at,
            updated_at=basket.last_modified or basket.created_at,
        )

        # Create items ORM
        items_orm = []
        for item in basket.items:
            item_orm = ShoppingCartItemORM(
                id=item.id,
                shopping_cart_id=item.shopping_cart_id,
                product_id=item.product_id,
                quantity=item.quantity,
                color=item.color,
                price=item.price,
                product_name=item.product_name,
                created_at=basket.created_at,
                updated_at=basket.last_modified or basket.created_at,
            )
            items_orm.append(item_orm)

        basket_orm.items = items_orm
        return basket_orm
