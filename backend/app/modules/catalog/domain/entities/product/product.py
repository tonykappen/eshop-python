"""Product domain model."""

from uuid import UUID

from app.core.domain.entity import Aggregate
from app.modules.catalog.domain.value_objects import SKU, Money
from pydantic import Field, field_validator


class Product(Aggregate):
    """Product aggregate following .NET Product class structure."""

    name: str = Field(..., description="Product name")
    sku: SKU = Field(..., description="Product SKU")
    category: list[str] = Field(default_factory=list, description="Product categories")
    description: str = Field(..., description="Product description")
    image_file: str = Field(
        default="", description="Product image file path (optional)"
    )
    price: Money = Field(..., description="Product price")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate product name is not empty."""
        if not v or not v.strip():
            raise ValueError("Product name is required and cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is not empty."""
        if not v or not v.strip():
            raise ValueError("Product description is required and cannot be empty")
        return v.strip()

    @field_validator("image_file")
    @classmethod
    def validate_image_file(cls, v: str | None) -> str:
        """Validate image file - allow empty string for optional images."""
        if v is None:
            return ""
        # Allow empty string (optional field)
        return v.strip() if v else ""

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: list[str]) -> list[str]:
        """Validate category list is not empty."""
        if not v:
            raise ValueError(
                "At least one category is required. Please add a category using the 'Add' button"
            )
        # Filter out empty strings and strip whitespace
        cleaned_categories = [cat.strip() for cat in v if cat and cat.strip()]
        if not cleaned_categories:
            raise ValueError(
                "At least one valid category is required. Categories cannot be empty or contain only whitespace"
            )
        return cleaned_categories

    @classmethod
    def create(
        cls,
        product_id: UUID,
        name: str,
        sku: str,
        category: list[str],
        description: str,
        image_file: str = "",
        price: Money | None = None,
    ) -> "Product":
        """
        Create a new product, matching .NET Product.Create static method.

        Args:
            product_id: Unique identifier for the product
            name: Product name (validated)
            sku: Product SKU (validated)
            category: List of categories (validated)
            description: Product description (validated)
            image_file: Image file path (optional, defaults to empty string)
            price: Product price (validated)

        Returns:
            Created Product instance with domain events

        Raises:
            ValueError: If any validation fails
        """
        if price is None:
            raise ValueError("price is required")

        # Validation happens in Pydantic validators
        # Use empty string if image_file is None or not provided
        image_file_value = image_file if image_file is not None else ""

        product = cls(
            id=product_id,
            name=name,
            sku=SKU(value=sku),
            category=category,
            description=description,
            image_file=image_file_value,
            price=price,
        )

        # Add domain event
        from app.modules.catalog.domain.domain_events.products.product_created_domain_event import \
            ProductCreatedDomainEvent

        product.add_domain_event(ProductCreatedDomainEvent(product=product))

        return product

    def update(
        self,
        name: str,
        category: list[str],
        description: str,
        image_file: str = "",
        price: Money | None = None,
    ) -> None:
        """
        Update product details, matching .NET Product.Update method.

        Args:
            name: New product name (validated)
            category: New categories list (validated)
            description: New description (validated)
            image_file: New image file path (optional, defaults to empty string)
            price: New price (validated)

        Raises:
            ValueError: If any validation fails
        """
        if price is None:
            raise ValueError("price is required")

        # Store old price for comparison
        old_price = self.price

        # Update fields (validation happens in Pydantic validators)
        # Use empty string if image_file is None or not provided
        image_file_value = image_file if image_file is not None else ""

        self.name = name
        self.category = category
        self.description = description
        self.image_file = image_file_value
        self.price = price

        # If price changed, add domain event
        if old_price != price:
            from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import \
                ProductPriceChangedDomainEvent

            self.add_domain_event(
                ProductPriceChangedDomainEvent(product=self, old_price=old_price)
            )

    def change_price(self, new_price: Money) -> None:
        """
        Change product price with domain event.

        Args:
            new_price: New price (validated)

        Raises:
            ValueError: If price validation fails
        """
        if new_price.is_zero() or not new_price.is_positive():
            raise ValueError("Product price must be positive")

        old_price = self.price
        self.price = new_price

        # Add domain event for price change
        if old_price != new_price:
            from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import \
                ProductPriceChangedDomainEvent

            self.add_domain_event(ProductPriceChangedDomainEvent(product=self))

    def add_category(self, category: str) -> None:
        """
        Add a category to the product.

        Args:
            category: Category to add (validated)

        Raises:
            ValueError: If category is invalid
        """
        if not category or not category.strip():
            raise ValueError("Category cannot be empty")

        cleaned_category = category.strip()
        if cleaned_category not in self.category:
            self.category.append(cleaned_category)

    def remove_category(self, category: str) -> None:
        """
        Remove a category from the product.

        Args:
            category: Category to remove

        Raises:
            ValueError: If trying to remove the last category
        """
        if not category or not category.strip():
            raise ValueError("Category cannot be empty")

        cleaned_category = category.strip()
        if cleaned_category in self.category:
            if len(self.category) <= 1:
                raise ValueError("Product must have at least one category")
            self.category.remove(cleaned_category)

    def update_categories(self, categories: list[str]) -> None:
        """
        Update all categories for the product.

        Args:
            categories: New list of categories (validated)

        Raises:
            ValueError: If validation fails
        """
        if not categories:
            raise ValueError("Product must have at least one category")

        # Clean and validate categories
        cleaned_categories = [cat.strip() for cat in categories if cat and cat.strip()]
        if not cleaned_categories:
            raise ValueError("Product must have at least one valid category")

        self.category = cleaned_categories

    def deactivate(self) -> None:
        """
        Deactivate the product.

        Raises:
            ValueError: If product is already deactivated
        """
        # Add domain event for deletion
        from app.modules.catalog.domain.domain_events.products.product_deleted_domain_event import \
            ProductDeletedDomainEvent

        self.add_domain_event(ProductDeletedDomainEvent(product=self))
