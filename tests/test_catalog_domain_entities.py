"""Comprehensive tests for Catalog domain entities."""

import pytest
from decimal import Decimal
from uuid import uuid4

from eshop.modules.catalog.domain.entities import (
    CatalogItem,
    CatalogCategory,
    CatalogBrand,
)


class TestCatalogItem:
    """Test CatalogItem domain entity."""

    def test_catalog_item_creation(self):
        """Test basic catalog item creation."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=10,
        )
        
        assert item.name == "Test Item"
        assert item.price == Decimal("99.99")
        assert item.stock_quantity == 10
        assert item.is_available is True
        assert item.description is None
        assert item.category_id is None
        assert item.brand_id is None

    def test_catalog_item_creation_with_all_fields(self):
        """Test catalog item creation with all optional fields."""
        category_id = uuid4()
        brand_id = uuid4()
        
        item = CatalogItem(
            name="Complete Item",
            description="A complete test item",
            price=Decimal("149.99"),
            stock_quantity=5,
            is_available=False,
            category_id=category_id,
            brand_id=brand_id,
        )
        
        assert item.name == "Complete Item"
        assert item.description == "A complete test item"
        assert item.price == Decimal("149.99")
        assert item.stock_quantity == 5
        assert item.is_available is False
        assert item.category_id == category_id
        assert item.brand_id == brand_id

    def test_catalog_item_price_validation(self):
        """Test that price must be positive."""
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            CatalogItem(
                name="Invalid Item",
                price=Decimal("0"),
            )

    def test_catalog_item_stock_quantity_default(self):
        """Test default stock quantity is 0."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
        )
        assert item.stock_quantity == 0

    def test_catalog_item_stock_quantity_validation(self):
        """Test that stock quantity cannot be negative."""
        with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
            CatalogItem(
                name="Test Item",
                price=Decimal("99.99"),
                stock_quantity=-1,
            )

    def test_update_stock_positive(self):
        """Test updating stock to a positive value."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=5,
        )
        
        item.update_stock(10)
        assert item.stock_quantity == 10

    def test_update_stock_zero(self):
        """Test updating stock to zero."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=5,
        )
        
        item.update_stock(0)
        assert item.stock_quantity == 0

    def test_update_stock_negative_raises_error(self):
        """Test that updating stock to negative value raises error."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=5,
        )
        
        with pytest.raises(ValueError, match="Stock quantity cannot be negative"):
            item.update_stock(-1)

    def test_reduce_stock_success(self):
        """Test successfully reducing stock."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=10,
        )
        
        item.reduce_stock(3)
        assert item.stock_quantity == 7

    def test_reduce_stock_insufficient_raises_error(self):
        """Test that reducing stock beyond available quantity raises error."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=5,
        )
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            item.reduce_stock(10)

    def test_reduce_stock_zero_quantity_raises_error(self):
        """Test that reducing stock by zero raises error."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=5,
        )
        
        with pytest.raises(ValueError, match="Quantity to reduce must be positive"):
            item.reduce_stock(0)

    def test_reduce_stock_negative_quantity_raises_error(self):
        """Test that reducing stock by negative quantity raises error."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=5,
        )
        
        with pytest.raises(ValueError, match="Quantity to reduce must be positive"):
            item.reduce_stock(-1)

    def test_increase_stock_success(self):
        """Test successfully increasing stock."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=5,
        )
        
        item.increase_stock(3)
        assert item.stock_quantity == 8

    def test_increase_stock_zero_quantity_raises_error(self):
        """Test that increasing stock by zero raises error."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=5,
        )
        
        with pytest.raises(ValueError, match="Quantity to increase must be positive"):
            item.increase_stock(0)

    def test_increase_stock_negative_quantity_raises_error(self):
        """Test that increasing stock by negative quantity raises error."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            stock_quantity=5,
        )
        
        with pytest.raises(ValueError, match="Quantity to increase must be positive"):
            item.increase_stock(-1)

    def test_mark_unavailable(self):
        """Test marking item as unavailable."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            is_available=True,
        )
        
        item.mark_unavailable()
        assert item.is_available is False

    def test_mark_available(self):
        """Test marking item as available."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
            is_available=False,
        )
        
        item.mark_available()
        assert item.is_available is True

    def test_update_price_success(self):
        """Test successfully updating price."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
        )
        
        item.update_price(Decimal("149.99"))
        assert item.price == Decimal("149.99")

    def test_update_price_zero_raises_error(self):
        """Test that updating price to zero raises error."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
        )
        
        with pytest.raises(ValueError, match="Price must be positive"):
            item.update_price(Decimal("0"))

    def test_update_price_negative_raises_error(self):
        """Test that updating price to negative value raises error."""
        item = CatalogItem(
            name="Test Item",
            price=Decimal("99.99"),
        )
        
        with pytest.raises(ValueError, match="Price must be positive"):
            item.update_price(Decimal("-10"))

    def test_catalog_item_equality(self):
        """Test catalog item equality based on ID."""
        item1 = CatalogItem(
            name="Test Item 1",
            price=Decimal("99.99"),
        )
        item2 = CatalogItem(
            name="Test Item 2",
            price=Decimal("149.99"),
        )
        
        # Different items should not be equal
        assert item1 != item2
        
        # Same item should be equal to itself
        assert item1 == item1

    def test_catalog_item_serialization(self):
        """Test catalog item serialization."""
        category_id = uuid4()
        brand_id = uuid4()
        
        item = CatalogItem(
            name="Test Item",
            description="Test description",
            price=Decimal("99.99"),
            stock_quantity=10,
            is_available=True,
            category_id=category_id,
            brand_id=brand_id,
        )
        
        item_dict = item.model_dump()
        assert item_dict["name"] == "Test Item"
        assert item_dict["description"] == "Test description"
        assert item_dict["price"] == Decimal("99.99")
        assert item_dict["stock_quantity"] == 10
        assert item_dict["is_available"] is True
        assert item_dict["category_id"] == category_id
        assert item_dict["brand_id"] == brand_id


class TestCatalogCategory:
    """Test CatalogCategory domain entity."""

    def test_catalog_category_creation(self):
        """Test basic catalog category creation."""
        category = CatalogCategory(
            name="Electronics",
            description="Electronic devices and accessories",
        )
        
        assert category.name == "Electronics"
        assert category.description == "Electronic devices and accessories"

    def test_catalog_category_creation_without_description(self):
        """Test catalog category creation without description."""
        category = CatalogCategory(name="Books")
        
        assert category.name == "Books"
        assert category.description is None

    def test_update_details_success(self):
        """Test successfully updating category details."""
        category = CatalogCategory(
            name="Old Name",
            description="Old description",
        )
        
        category.update_details("New Name", "New description")
        assert category.name == "New Name"
        assert category.description == "New description"

    def test_update_details_name_only(self):
        """Test updating only the name."""
        category = CatalogCategory(
            name="Old Name",
            description="Old description",
        )
        
        category.update_details("New Name")
        assert category.name == "New Name"
        assert category.description is None  # Description is not preserved when not provided

    def test_update_details_empty_name_raises_error(self):
        """Test that updating with empty name raises error."""
        category = CatalogCategory(name="Valid Name")
        
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            category.update_details("")

    def test_update_details_whitespace_name_raises_error(self):
        """Test that updating with whitespace-only name raises error."""
        category = CatalogCategory(name="Valid Name")
        
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            category.update_details("   ")

    def test_update_details_trims_whitespace(self):
        """Test that name is trimmed of whitespace."""
        category = CatalogCategory(name="Old Name")
        
        category.update_details("  New Name  ")
        assert category.name == "New Name"

    def test_catalog_category_equality(self):
        """Test catalog category equality based on ID."""
        category1 = CatalogCategory(name="Category 1")
        category2 = CatalogCategory(name="Category 2")
        
        # Different categories should not be equal
        assert category1 != category2
        
        # Same category should be equal to itself
        assert category1 == category1

    def test_catalog_category_serialization(self):
        """Test catalog category serialization."""
        category = CatalogCategory(
            name="Test Category",
            description="Test description",
        )
        
        category_dict = category.model_dump()
        assert category_dict["name"] == "Test Category"
        assert category_dict["description"] == "Test description"


class TestCatalogBrand:
    """Test CatalogBrand domain entity."""

    def test_catalog_brand_creation(self):
        """Test basic catalog brand creation."""
        brand = CatalogBrand(
            name="Apple",
            description="Technology company",
            logo_url="https://example.com/apple-logo.png",
        )
        
        assert brand.name == "Apple"
        assert brand.description == "Technology company"
        assert brand.logo_url == "https://example.com/apple-logo.png"

    def test_catalog_brand_creation_minimal(self):
        """Test catalog brand creation with minimal fields."""
        brand = CatalogBrand(name="Samsung")
        
        assert brand.name == "Samsung"
        assert brand.description is None
        assert brand.logo_url is None

    def test_update_details_success(self):
        """Test successfully updating brand details."""
        brand = CatalogBrand(
            name="Old Name",
            description="Old description",
            logo_url="https://old-logo.png",
        )
        
        brand.update_details(
            "New Name",
            "New description",
            "https://new-logo.png",
        )
        assert brand.name == "New Name"
        assert brand.description == "New description"
        assert brand.logo_url == "https://new-logo.png"

    def test_update_details_partial(self):
        """Test updating only some fields."""
        brand = CatalogBrand(
            name="Old Name",
            description="Old description",
            logo_url="https://old-logo.png",
        )
        
        brand.update_details("New Name")
        assert brand.name == "New Name"
        assert brand.description is None  # Description is not preserved when not provided
        assert brand.logo_url is None  # Logo URL is not preserved when not provided

    def test_update_details_empty_name_raises_error(self):
        """Test that updating with empty name raises error."""
        brand = CatalogBrand(name="Valid Name")
        
        with pytest.raises(ValueError, match="Brand name cannot be empty"):
            brand.update_details("")

    def test_update_details_whitespace_name_raises_error(self):
        """Test that updating with whitespace-only name raises error."""
        brand = CatalogBrand(name="Valid Name")
        
        with pytest.raises(ValueError, match="Brand name cannot be empty"):
            brand.update_details("   ")

    def test_update_details_trims_whitespace(self):
        """Test that name is trimmed of whitespace."""
        brand = CatalogBrand(name="Old Name")
        
        brand.update_details("  New Name  ")
        assert brand.name == "New Name"

    def test_catalog_brand_equality(self):
        """Test catalog brand equality based on ID."""
        brand1 = CatalogBrand(name="Brand 1")
        brand2 = CatalogBrand(name="Brand 2")
        
        # Different brands should not be equal
        assert brand1 != brand2
        
        # Same brand should be equal to itself
        assert brand1 == brand1

    def test_catalog_brand_serialization(self):
        """Test catalog brand serialization."""
        brand = CatalogBrand(
            name="Test Brand",
            description="Test description",
            logo_url="https://test-logo.png",
        )
        
        brand_dict = brand.model_dump()
        assert brand_dict["name"] == "Test Brand"
        assert brand_dict["description"] == "Test description"
        assert brand_dict["logo_url"] == "https://test-logo.png"
