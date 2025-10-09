"""Product domain model."""

from uuid import UUID

from pydantic import Field, field_validator

from app.core.domain.entity import Aggregate
from app.modules.catalog.domain.value_objects import Money, SKU


class Product(Aggregate):
    """Product aggregate following .NET Product class structure."""

    name: str = Field(..., description="Product name")
    sku: SKU = Field(..., description="Product SKU")
    category: list[str] = Field(default_factory=list, description="Product categories")
    description: str = Field(..., description="Product description")
    image_file: str = Field(..., description="Product image file path")
    price: Money = Field(..., description="Product price")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate product name is not empty."""
        if not v or not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip()

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
        sku: str,
        category: list[str],
        description: str,
        image_file: str,
        price: Money,
    ) -> "Product":
        """
        Create a new product, matching .NET Product.Create static method.
        
        Args:
            product_id: Unique identifier for the product
            name: Product name (validated)
            sku: Product SKU (validated)
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
            sku=SKU(value=sku),
            category=category,
            description=description,
            image_file=image_file,
            price=price,
        )

        # Add domain event
        from app.modules.catalog.domain.product.domain_events.product_created_domain_event import (
            ProductCreatedDomainEvent,
        )

        product.add_domain_event(ProductCreatedDomainEvent(product=product))

        return product

    def update(
        self,
        name: str,
        category: list[str],
        description: str,
        image_file: str,
        price: Money,
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

        # Increment version for any update
        self.increment_version()

        # If price changed, add domain event
        if old_price != price:
            from app.modules.catalog.domain.product.domain_events.product_price_changed_domain_event import (
                ProductPriceChangedDomainEvent,
            )

            self.add_domain_event(ProductPriceChangedDomainEvent(product=self))

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
        self.increment_version()

        # Add domain event for price change
        if old_price != new_price:
            from app.modules.catalog.domain.product.domain_events.product_price_changed_domain_event import (
                ProductPriceChangedDomainEvent,
            )
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
            self.increment_version()

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
            self.increment_version()

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
        self.increment_version()

    def deactivate(self) -> None:
        """
        Deactivate the product.
        
        Raises:
            ValueError: If product is already deactivated
        """
        # Add domain event for deactivation
        from app.modules.catalog.domain.product.domain_events.product_deactivated_domain_event import (
            ProductDeactivatedDomainEvent,
        )
        self.add_domain_event(ProductDeactivatedDomainEvent(product=self))


