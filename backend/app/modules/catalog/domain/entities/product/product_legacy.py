"""Product domain models."""

from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from app.core.domain.entity import Aggregate


class Product(Aggregate):
    """Product aggregate following .NET Product class structure."""

    name: str = Field(..., description="Product name")
    category: list[str] = Field(default_factory=list, description="Product categories")
    description: str = Field(..., description="Product description")
    image_file: str = Field(..., description="Product image file path")
    price: Decimal = Field(..., description="Product price", gt=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate product name is not empty."""
        if not v or not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip()

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError("Product price must be positive")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is not empty."""
        if not v or not v.strip():
            raise ValueError("Product description cannot be empty")
        return v.strip()

    @field_validator("image_file")
    @classmethod
    def validate_image_file(cls, v: str) -> str:
        """Validate image file is not empty."""
        if not v or not v.strip():
            raise ValueError("Product image file cannot be empty")
        return v.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: list[str]) -> list[str]:
        """Validate category list is not empty."""
        if not v:
            raise ValueError("Product must have at least one category")
        # Filter out empty strings and strip whitespace
        cleaned_categories = [cat.strip() for cat in v if cat and cat.strip()]
        if not cleaned_categories:
            raise ValueError("Product must have at least one valid category")
        return cleaned_categories

    @classmethod
    def create(
        cls,
        product_id: UUID,
        name: str,
        category: list[str],
        description: str,
        image_file: str,
        price: Decimal,
    ) -> "Product":
        """
        Create a new product, matching .NET Product.Create static method.

        Args:
            product_id: Unique identifier for the product
            name: Product name (validated)
            category: List of categories (validated)
            description: Product description (validated)
            image_file: Image file path (validated)
            price: Product price (validated)

        Returns:
            Created Product instance with domain events

        Raises:
            ValueError: If any validation fails
        """
        # Validation happens in Pydantic validators
        product = cls(
            id=product_id,
            name=name,
            category=category,
            description=description,
            image_file=image_file,
            price=price,
        )

        # Add domain event - use string reference to avoid circular import issues
        from app.modules.catalog.domain.events import ProductCreatedEvent

        product.add_domain_event(ProductCreatedEvent(product=product))

        return product

    def update(
        self,
        name: str,
        category: list[str],
        description: str,
        image_file: str,
        price: Decimal,
    ) -> None:
        """
        Update product details, matching .NET Product.Update method.

        Args:
            name: New product name (validated)
            category: New categories list (validated)
            description: New description (validated)
            image_file: New image file path (validated)
            price: New price (validated)

        Raises:
            ValueError: If any validation fails
        """
        # Store old price for comparison
        old_price = self.price

        # Update fields (validation happens in Pydantic validators)
        self.name = name
        self.category = category
        self.description = description
        self.image_file = image_file
        self.price = price

        # If price changed, add domain event
        if old_price != price:
            from app.modules.catalog.domain.events import ProductPriceChangedEvent

            self.add_domain_event(ProductPriceChangedEvent(product=self))

    def change_price(self, new_price: Decimal) -> None:
        """
        Change product price with domain event.

        Args:
            new_price: New price (validated)

        Raises:
            ValueError: If price validation fails
        """
        if new_price <= 0:
            raise ValueError("Product price must be positive")

        old_price = self.price
        self.price = new_price

        # Add domain event for price change
        if old_price != new_price:
            from app.modules.catalog.domain.events import ProductPriceChangedEvent

            self.add_domain_event(ProductPriceChangedEvent(product=self))

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
