"""Initial seed data for catalog module."""

import logging
from decimal import Decimal
from uuid import uuid4

from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.value_objects import Money

logger = logging.getLogger(__name__)


class CatalogInitialData:
    """Initial seed data for catalog module."""

    @staticmethod
    def get_initial_products() -> list[Product]:
        """
        Get initial products for seeding.

        Returns:
            List of initial products
        """
        products = []

        # Electronics products
        products.extend(
            [
                Product.create(
                    product_id=uuid4(),
                    name="iPhone 15 Pro",
                    sku="IPHONE-15-PRO-256",
                    category=["Electronics", "Smartphones"],
                    description="Latest iPhone with advanced camera system and A17 Pro chip",
                    image_file="/images/iphone-15-pro.jpg",
                    price=Money(amount=Decimal("999.00"), currency="USD"),
                ),
                Product.create(
                    product_id=uuid4(),
                    name="Samsung Galaxy S24 Ultra",
                    sku="SAMSUNG-S24-ULTRA-512",
                    category=["Electronics", "Smartphones"],
                    description="Premium Android smartphone with S Pen and advanced AI features",
                    image_file="/images/samsung-s24-ultra.jpg",
                    price=Money(amount=Decimal("1199.00"), currency="USD"),
                ),
                Product.create(
                    product_id=uuid4(),
                    name="MacBook Pro 16-inch",
                    sku="MACBOOK-PRO-16-M3",
                    category=["Electronics", "Laptops"],
                    description="Powerful laptop with M3 chip for professional work",
                    image_file="/images/macbook-pro-16.jpg",
                    price=Money(amount=Decimal("2499.00"), currency="USD"),
                ),
                Product.create(
                    product_id=uuid4(),
                    name="Dell XPS 15",
                    sku="DELL-XPS-15-2024",
                    category=["Electronics", "Laptops"],
                    description="Premium Windows laptop with stunning display",
                    image_file="/images/dell-xps-15.jpg",
                    price=Money(amount=Decimal("1899.00"), currency="USD"),
                ),
            ]
        )

        # Clothing products
        products.extend(
            [
                Product.create(
                    product_id=uuid4(),
                    name="Nike Air Max 270",
                    sku="NIKE-AIR-MAX-270-BLK",
                    category=["Clothing", "Shoes"],
                    description="Comfortable running shoes with Air Max technology",
                    image_file="/images/nike-air-max-270.jpg",
                    price=Money(amount=Decimal("150.00"), currency="USD"),
                ),
                Product.create(
                    product_id=uuid4(),
                    name="Adidas Ultraboost 22",
                    sku="ADIDAS-ULTRABOOST-22-WHT",
                    category=["Clothing", "Shoes"],
                    description="High-performance running shoes with Boost technology",
                    image_file="/images/adidas-ultraboost-22.jpg",
                    price=Money(amount=Decimal("180.00"), currency="USD"),
                ),
                Product.create(
                    product_id=uuid4(),
                    name="Levi's 501 Original Jeans",
                    sku="LEVIS-501-ORIGINAL-BLU",
                    category=["Clothing", "Jeans"],
                    description="Classic straight-fit jeans in original blue",
                    image_file="/images/levis-501-original.jpg",
                    price=Money(amount=Decimal("89.00"), currency="USD"),
                ),
            ]
        )

        # Home & Garden products
        products.extend(
            [
                Product.create(
                    product_id=uuid4(),
                    name="Dyson V15 Detect Vacuum",
                    sku="DYSON-V15-DETECT",
                    category=["Home & Garden", "Cleaning"],
                    description="Advanced cordless vacuum with laser dust detection",
                    image_file="/images/dyson-v15-detect.jpg",
                    price=Money(amount=Decimal("749.00"), currency="USD"),
                ),
                Product.create(
                    product_id=uuid4(),
                    name="Instant Pot Duo 7-in-1",
                    sku="INSTANT-POT-DUO-7IN1",
                    category=["Home & Garden", "Kitchen"],
                    description="Multi-functional pressure cooker for quick meals",
                    image_file="/images/instant-pot-duo.jpg",
                    price=Money(amount=Decimal("99.00"), currency="USD"),
                ),
                Product.create(
                    product_id=uuid4(),
                    name="Philips Hue Smart Bulb Starter Kit",
                    sku="PHILIPS-HUE-STARTER-KIT",
                    category=["Home & Garden", "Smart Home"],
                    description="Smart lighting system with app control",
                    image_file="/images/philips-hue-starter.jpg",
                    price=Money(amount=Decimal("199.00"), currency="USD"),
                ),
            ]
        )

        # Books & Media products
        products.extend(
            [
                Product.create(
                    product_id=uuid4(),
                    name="The Psychology of Money",
                    sku="BOOK-PSYCHOLOGY-MONEY",
                    category=["Books & Media", "Business"],
                    description="Timeless lessons on wealth, greed, and happiness",
                    image_file="/images/psychology-of-money.jpg",
                    price=Money(amount=Decimal("16.99"), currency="USD"),
                ),
                Product.create(
                    product_id=uuid4(),
                    name="Atomic Habits",
                    sku="BOOK-ATOMIC-HABITS",
                    category=["Books & Media", "Self-Help"],
                    description="An Easy & Proven Way to Build Good Habits & Break Bad Ones",
                    image_file="/images/atomic-habits.jpg",
                    price=Money(amount=Decimal("18.99"), currency="USD"),
                ),
            ]
        )

        # Sports & Outdoors products
        products.extend(
            [
                Product.create(
                    product_id=uuid4(),
                    name="Yeti Rambler 20oz Tumbler",
                    sku="YETI-RAMBLER-20OZ",
                    category=["Sports & Outdoors", "Drinkware"],
                    description="Insulated tumbler that keeps drinks cold for hours",
                    image_file="/images/yeti-rambler-20oz.jpg",
                    price=Money(amount=Decimal("35.00"), currency="USD"),
                ),
                Product.create(
                    product_id=uuid4(),
                    name="Patagonia Better Sweater Jacket",
                    sku="PATAGONIA-BETTER-SWEATER",
                    category=["Sports & Outdoors", "Outerwear"],
                    description="Fleece jacket made from recycled polyester",
                    image_file="/images/patagonia-better-sweater.jpg",
                    price=Money(amount=Decimal("149.00"), currency="USD"),
                ),
            ]
        )

        logger.info(f"Generated {len(products)} initial products")
        return products

    @staticmethod
    def get_product_categories() -> list[str]:
        """
        Get list of product categories.

        Returns:
            List of category names
        """
        return [
            "Electronics",
            "Clothing",
            "Home & Garden",
            "Books & Media",
            "Sports & Outdoors",
            "Smartphones",
            "Laptops",
            "Shoes",
            "Jeans",
            "Cleaning",
            "Kitchen",
            "Smart Home",
            "Business",
            "Self-Help",
            "Drinkware",
            "Outerwear",
        ]

    @staticmethod
    def get_sample_skus() -> list[str]:
        """
        Get sample SKUs for testing.

        Returns:
            List of sample SKUs
        """
        return [
            "IPHONE-15-PRO-256",
            "SAMSUNG-S24-ULTRA-512",
            "MACBOOK-PRO-16-M3",
            "DELL-XPS-15-2024",
            "NIKE-AIR-MAX-270-BLK",
            "ADIDAS-ULTRABOOST-22-WHT",
            "LEVIS-501-ORIGINAL-BLU",
            "DYSON-V15-DETECT",
            "INSTANT-POT-DUO-7IN1",
            "PHILIPS-HUE-STARTER-KIT",
            "BOOK-PSYCHOLOGY-MONEY",
            "BOOK-ATOMIC-HABITS",
            "YETI-RAMBLER-20OZ",
            "PATAGONIA-BETTER-SWEATER",
        ]
