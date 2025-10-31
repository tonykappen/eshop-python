"""Comprehensive tests for Catalog application handlers."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.mediator.cancellation import CancellationToken
from app.modules.catalog.application.handlers.create_product_handler import (
    CreateProductCommand,
    CreateProductHandler,
    CreateProductResult,
)
from app.modules.catalog.contracts.product.dtos import ProductDto
from app.modules.catalog.domain.exceptions import (
    ProductCreationError,
    ProductValidationError,
)


class TestCreateProductCommand:
    """Test CreateProductCommand."""

    def test_create_product_command_initialization(self):
        """Test CreateProductCommand initialization."""
        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        command = CreateProductCommand(product=product_dto)

        assert command.product == product_dto
        assert command.product.name == "Test Product"
        assert command.product.category == ["Electronics"]


class TestCreateProductResult:
    """Test CreateProductResult."""

    def test_create_product_result_initialization(self):
        """Test CreateProductResult initialization."""
        product_id = uuid4()
        result = CreateProductResult(id=product_id)

        assert result.id == product_id


class TestCreateProductHandler:
    """Test CreateProductHandler."""

    def test_handler_initialization(self):
        """Test CreateProductHandler initialization."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        assert handler.db_context == mock_db_context

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful product creation."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        command = CreateProductCommand(product=product_dto)
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, CreateProductResult)
        assert isinstance(result.id, UUID)

    @pytest.mark.asyncio
    async def test_handle_empty_name_raises_validation_error(self):
        """Test that empty product name raises validation error."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="",  # Empty name
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        command = CreateProductCommand(product=product_dto)
        token = CancellationToken()

        with pytest.raises(ProductValidationError, match="Product name is required"):
            await handler.handle(command, token)

    @pytest.mark.asyncio
    async def test_handle_whitespace_name_raises_validation_error(self):
        """Test that whitespace-only product name raises validation error."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="   ",  # Whitespace only
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        command = CreateProductCommand(product=product_dto)
        token = CancellationToken()

        with pytest.raises(ProductValidationError, match="Product name is required"):
            await handler.handle(command, token)

    @pytest.mark.asyncio
    async def test_handle_zero_price_raises_validation_error(self):
        """Test that zero price raises validation error."""
        mock_db_context = MagicMock()
        CreateProductHandler(db_context=mock_db_context)

        # ProductDto validation happens at creation time, not in handler
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            ProductDto(
                id=uuid4(),
                name="Test Product",
                category=["Electronics"],
                description="A test product",
                image_file="test.jpg",
                price=Decimal("0"),  # Zero price
            )

    @pytest.mark.asyncio
    async def test_handle_negative_price_raises_validation_error(self):
        """Test that negative price raises validation error."""
        mock_db_context = MagicMock()
        CreateProductHandler(db_context=mock_db_context)

        # ProductDto validation happens at creation time, not in handler
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            ProductDto(
                id=uuid4(),
                name="Test Product",
                category=["Electronics"],
                description="A test product",
                image_file="test.jpg",
                price=Decimal("-10"),  # Negative price
            )

    @pytest.mark.asyncio
    async def test_handle_cancellation_before_processing(self):
        """Test cancellation before processing."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        command = CreateProductCommand(product=product_dto)
        token = CancellationToken()

        # Cancel the token before processing
        token.cancel()

        with pytest.raises(Exception, match="Operation was cancelled"):
            await handler.handle(command, token)

    @pytest.mark.asyncio
    async def test_handle_database_save_failure(self):
        """Test database save failure handling."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        command = CreateProductCommand(product=product_dto)
        token = CancellationToken()

        # Mock the _save_to_database method to raise an exception
        handler._save_to_database = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        with pytest.raises(Exception, match="Database connection failed"):
            await handler.handle(command, token)

    @pytest.mark.asyncio
    async def test_handle_cancellation_during_save(self):
        """Test cancellation during database save."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        command = CreateProductCommand(product=product_dto)
        token = CancellationToken()

        # Mock the _save_to_database method to check cancellation
        async def mock_save_with_cancellation(
            _product,
            cancellation_token,  # noqa: ARG001
        ):
            cancellation_token.throw_if_cancellation_requested()
            # Simulate some work
            await asyncio.sleep(0.01)
            cancellation_token.throw_if_cancellation_requested()

        handler._save_to_database = mock_save_with_cancellation

        # Cancel the token after a short delay
        async def cancel_after_delay():
            await asyncio.sleep(0.005)
            token.cancel()

        # Start cancellation task
        import asyncio

        asyncio.create_task(cancel_after_delay())

        with pytest.raises(Exception, match="Operation was cancelled"):
            await handler.handle(command, token)

    def test_create_new_product_success(self):
        """Test successful product creation from DTO."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        product = handler._create_new_product(product_dto)

        assert product.name == "Test Product"
        assert product.category == ["Electronics"]
        assert product.description == "A test product"
        assert product.image_file == "test.jpg"
        assert product.price == Decimal("99.99")

    def test_create_new_product_empty_name_raises_error(self):
        """Test that empty name raises validation error."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="",  # Empty name
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        with pytest.raises(ProductValidationError, match="Product name is required"):
            handler._create_new_product(product_dto)

    def test_create_new_product_whitespace_name_raises_error(self):
        """Test that whitespace-only name raises validation error."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="   ",  # Whitespace only
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        with pytest.raises(ProductValidationError, match="Product name is required"):
            handler._create_new_product(product_dto)

    def test_create_new_product_zero_price_raises_error(self):
        """Test that zero price raises validation error."""
        mock_db_context = MagicMock()
        CreateProductHandler(db_context=mock_db_context)

        # ProductDto validation happens at creation time, not in handler
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            ProductDto(
                id=uuid4(),
                name="Test Product",
                category=["Electronics"],
                description="A test product",
                image_file="test.jpg",
                price=Decimal("0"),  # Zero price
            )

    def test_create_new_product_negative_price_raises_error(self):
        """Test that negative price raises validation error."""
        mock_db_context = MagicMock()
        CreateProductHandler(db_context=mock_db_context)

        # ProductDto validation happens at creation time, not in handler
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            ProductDto(
                id=uuid4(),
                name="Test Product",
                category=["Electronics"],
                description="A test product",
                image_file="test.jpg",
                price=Decimal("-10"),  # Negative price
            )

    @pytest.mark.asyncio
    async def test_save_to_database_success(self):
        """Test successful database save."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        product = handler._create_new_product(product_dto)
        token = CancellationToken()

        # Should not raise any exception
        await handler._save_to_database(product, token)

    @pytest.mark.asyncio
    async def test_save_to_database_failure(self):
        """Test database save failure."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        product = handler._create_new_product(product_dto)
        token = CancellationToken()

        # Mock the sleep to raise an exception
        import asyncio

        original_sleep = asyncio.sleep

        async def mock_sleep(delay):  # noqa: ARG001
            raise Exception("Database connection failed")

        asyncio.sleep = mock_sleep

        try:
            with pytest.raises(
                ProductCreationError, match="Failed to save product to database"
            ):
                await handler._save_to_database(product, token)
        finally:
            # Restore original sleep
            asyncio.sleep = original_sleep

    @pytest.mark.asyncio
    async def test_save_to_database_cancellation_check(self):
        """Test that save_to_database checks for cancellation."""
        mock_db_context = MagicMock()
        handler = CreateProductHandler(db_context=mock_db_context)

        product_dto = ProductDto(
            id=uuid4(),
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        product = handler._create_new_product(product_dto)
        token = CancellationToken()

        # Cancel the token
        token.cancel()

        with pytest.raises(Exception, match="Operation was cancelled"):
            await handler._save_to_database(product, token)
