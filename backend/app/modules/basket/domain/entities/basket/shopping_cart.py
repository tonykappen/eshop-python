"""ShoppingCart aggregate root - represents a user's shopping cart."""

from decimal import Decimal
from uuid import UUID

from app.core.domain.entity import Aggregate
from pydantic import Field, field_validator

from .shopping_cart_item import ShoppingCartItem


class ShoppingCart(Aggregate):
    """ShoppingCart aggregate following .NET ShoppingCart class structure."""

    user_name: str = Field(..., description="User name (owner of the cart)")
    items: list[ShoppingCartItem] = Field(
        default_factory=list, description="Shopping cart items"
    )

    @field_validator("user_name")
    @classmethod
    def validate_user_name(cls, v: str) -> str:
        """Validate user name is not empty."""
        if not v or not v.strip():
            raise ValueError("User name is required and cannot be empty")
        return v.strip()

    @property
    def total_price(self) -> Decimal:
        """
        Calculate total price of all items.

        Returns:
            Total price as Decimal
        """
        return sum(
            (item.price * Decimal(item.quantity) for item in self.items),
            Decimal(0),
        )

    @classmethod
    def create(cls, cart_id: UUID, user_name: str) -> "ShoppingCart":
        """
        Create a new shopping cart, matching .NET ShoppingCart.Create static method.

        Args:
            cart_id: Unique identifier for the cart
            user_name: User name (validated)

        Returns:
            Created ShoppingCart instance

        Raises:
            ValueError: If user name is invalid
        """
        if not user_name or not user_name.strip():
            raise ValueError("User name is required and cannot be empty")

        return cls(id=cart_id, user_name=user_name.strip(), items=[])

    def add_item(
        self,
        product_id: UUID,
        quantity: int,
        color: str,
        price: Decimal,
        product_name: str,
    ) -> None:
        """
        Add an item to the shopping cart, matching .NET AddItem method.

        If the item already exists (same product_id), increment the quantity.
        Otherwise, add a new item.

        Args:
            product_id: Product ID
            quantity: Quantity to add (must be > 0)
            color: Item color
            price: Item price (must be > 0)
            product_name: Product name

        Raises:
            ValueError: If quantity or price is invalid
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        if price <= 0:
            raise ValueError("Price must be greater than 0")

        # Check if item already exists
        existing_item = next(
            (item for item in self.items if item.product_id == product_id), None
        )

        if existing_item:
            # Increment quantity
            existing_item.quantity += quantity
        else:
            # Create new item
            from uuid import uuid4

            new_item = ShoppingCartItem(
                id=uuid4(),
                shopping_cart_id=self.id,
                product_id=product_id,
                quantity=quantity,
                color=color,
                price=price,
                product_name=product_name,
            )
            self.items.append(new_item)

        # Increment version for any change
        self.increment_version()

    def remove_item(self, product_id: UUID) -> None:
        """
        Remove an item from the shopping cart, matching .NET RemoveItem method.

        Args:
            product_id: Product ID to remove

        Note:
            If the item doesn't exist, this is a no-op (matches .NET behavior)
        """
        existing_item = next(
            (item for item in self.items if item.product_id == product_id), None
        )

        if existing_item:
            self.items.remove(existing_item)
            # Increment version for any change
            self.increment_version()
