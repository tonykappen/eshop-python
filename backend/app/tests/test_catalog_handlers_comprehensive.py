"""Comprehensive tests for Catalog handlers with DDD structure."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.mediator.cancellation import CancellationToken
from app.modules.catalog.application.handlers.create_product_handler import (
    CreateProductCommand,
    CreateProductHandler,
    CreateProductResult,
)
from app.modules.catalog.application.handlers.delete_product_handler import (
    DeleteProductCommand,
    DeleteProductHandler,
    DeleteProductResult,
)
from app.modules.catalog.application.handlers.get_product_by_id_handler import (
    GetProductByIdHandler,
)
from app.modules.catalog.application.handlers.get_products_handler import (
    GetProductsHandler,
)
from app.modules.catalog.application.handlers.update_product_handler import (
    UpdateProductCommand,
    UpdateProductHandler,
    UpdateProductResult,
)
from app.modules.catalog.contracts.products.dtos import ProductDto
from app.modules.catalog.contracts.products.features.get_product_by_id import (
    GetProductByIdQuery,
    GetProductByIdResult,
)
from app.modules.catalog.domain.exceptions import (
    ProductCreationError,
    ProductDeleteError,
    ProductNotFoundError,
    ProductUpdateError,
    ProductValidationError,
)
from app.modules.catalog.infrastructure.product_repository import ProductRepository


class TestCreateProductHandler:
    """Test CreateProductHandler with comprehensive scenarios."""

    @pytest.fixture
    def handler(self):
        """Create handler instance."""
        return CreateProductHandler()

    @pytest.fixture
    def sample_product_dto(self):
        """Sample ProductDto for testing."""
        return ProductDto(
            id=uuid4(),
            name="Test Product",
            description="A test product description",
            price=Decimal("99.99"),
            picture_url="https://example.com/image.jpg",
            category=["Electronics", "Gadgets"]
        )

    @pytest.fixture
    def sample_command(self, sample_product_dto):
        """Sample CreateProductCommand for testing."""
        return CreateProductCommand(
            name=sample_product_dto.name,
            description=sample_product_dto.description,
            price=float(sample_product_dto.price),  # Convert Decimal to float
            picture_url=sample_product_dto.picture_url,
            category=sample_product_dto.category,
        )

    @pytest.fixture
    def mock_repository(self):
        """Mock ProductRepository."""
        return AsyncMock(spec=ProductRepository)

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_handle_success(self, handler, sample_command, mock_repository, mock_session):
        """Test successful product creation."""
        with patch('app.modules.catalog.application.handlers.create_product_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            # Mock repository creation
            with patch('app.modules.catalog.application.handlers.create_product_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                from app.modules.catalog.domain.models import Product
                created_product = Product(
                    id=uuid4(),
                    name=sample_command.name,
                    description=sample_command.description,
                    price=Decimal(str(sample_command.price)),
                    image_file=sample_command.picture_url,
                    category=sample_command.category
                )
                mock_repository.add.return_value = created_product

                result = await handler.handle(sample_command, CancellationToken())

                assert isinstance(result, CreateProductResult)
                assert result.id == created_product.id
                mock_repository.add.assert_called_once()
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_database_error(self, handler, sample_command, mock_repository, mock_session):
        """Test product creation with database error."""
        with patch('app.modules.catalog.application.handlers.create_product_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.create_product_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                mock_repository.add.side_effect = Exception("Database error")

                with pytest.raises(ProductCreationError) as exc_info:
                    await handler.handle(sample_command, CancellationToken())

                assert "Failed to save product to database" in str(exc_info.value)
                mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_validation_error(self, handler, mock_repository, mock_session):
        """Test product creation with validation error."""
        # Create invalid command with empty name
        invalid_command = CreateProductCommand(
            name="",  # Invalid empty name
            description="Test description",
            price=99.99,  # Use float instead of Decimal
            picture_url="https://example.com/image.jpg",
            category=["Electronics"],
        )

        with pytest.raises(ProductValidationError) as exc_info:
            await handler.handle(invalid_command, CancellationToken())

        assert "Command validation failed" in str(exc_info.value)
        assert "Name is required" in str(exc_info.value)


class TestGetProductByIdHandler:
    """Test GetProductByIdHandler with comprehensive scenarios."""

    @pytest.fixture
    def handler(self):
        """Create handler instance."""
        return GetProductByIdHandler()

    @pytest.fixture
    def sample_product_dto(self):
        """Sample ProductDto for testing."""
        return ProductDto(
            id=uuid4(),
            name="Test Product",
            description="A test product description",
            price=Decimal("99.99"),
            picture_url="https://example.com/image.jpg",
            category=["Electronics", "Gadgets"]
        )

    @pytest.fixture
    def sample_query(self):
        """Sample GetProductByIdQuery for testing."""
        return GetProductByIdQuery(id=uuid4())

    @pytest.fixture
    def mock_repository(self):
        """Mock ProductRepository."""
        return AsyncMock(spec=ProductRepository)

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_handle_success(self, handler, sample_query, sample_product_dto, mock_repository, mock_session):
        """Test successful product retrieval."""
        with patch('app.modules.catalog.application.handlers.get_product_by_id_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.get_product_by_id_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                
                # Mock the product entity
                mock_product = MagicMock()
                mock_product.id = sample_product_dto.id
                mock_product.name = sample_product_dto.name
                mock_product.description = sample_product_dto.description
                mock_product.price = sample_product_dto.price
                mock_product.image_file = sample_product_dto.picture_url
                mock_product.category = sample_product_dto.category
                
                mock_repository.get_by_id.return_value = mock_product

                result = await handler.handle(sample_query, CancellationToken())

                assert isinstance(result, GetProductByIdResult)
                assert result.product is not None
                assert result.product.id == sample_product_dto.id
                assert result.product.name == sample_product_dto.name

    @pytest.mark.asyncio
    async def test_handle_product_not_found(self, handler, sample_query, mock_repository, mock_session):
        """Test product retrieval when product not found."""
        with patch('app.modules.catalog.application.handlers.get_product_by_id_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.get_product_by_id_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                mock_repository.get_by_id.return_value = None

                with pytest.raises(ProductNotFoundError) as exc_info:
                    await handler.handle(sample_query, CancellationToken())

                assert str(sample_query.id) in str(exc_info.value)


class TestUpdateProductHandler:
    """Test UpdateProductHandler with comprehensive scenarios."""

    @pytest.fixture
    def handler(self):
        """Create handler instance."""
        return UpdateProductHandler()

    @pytest.fixture
    def sample_command(self):
        """Sample UpdateProductCommand for testing."""
        return UpdateProductCommand(
            id=uuid4(),
            name="Updated Product",
            description="Updated description",
            price=Decimal("149.99"),
            picture_url="https://example.com/updated.jpg",
            category=["Electronics", "Updated"],
        )

    @pytest.fixture
    def mock_repository(self):
        """Mock ProductRepository."""
        return AsyncMock(spec=ProductRepository)

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_handle_success(self, handler, sample_command, mock_repository, mock_session):
        """Test successful product update."""
        with patch('app.modules.catalog.application.handlers.update_product_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.update_product_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                
                # Mock existing product
                mock_product = MagicMock()
                mock_product.id = sample_command.id
                mock_product.name = "Original Name"
                mock_product.description = "Original Description"
                mock_product.price = Decimal("99.99")
                mock_product.image_file = "original.jpg"
                mock_product.category = ["Original"]
                
                mock_repository.get_by_id.return_value = mock_product

                result = await handler.handle(sample_command, CancellationToken())

                assert isinstance(result, UpdateProductResult)
                assert result.is_success is True
                mock_repository.update.assert_called_once()
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_product_not_found(self, handler, sample_command, mock_repository, mock_session):
        """Test product update when product not found."""
        with patch('app.modules.catalog.application.handlers.update_product_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.update_product_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                mock_repository.get_by_id.return_value = None

                with pytest.raises(ProductNotFoundError) as exc_info:
                    await handler.handle(sample_command, CancellationToken())

                assert str(sample_command.id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_database_error(self, handler, sample_command, mock_repository, mock_session):
        """Test product update with database error."""
        with patch('app.modules.catalog.application.handlers.update_product_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.update_product_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                
                # Mock existing product
                mock_product = MagicMock()
                mock_repository.get_by_id.return_value = mock_product
                mock_repository.update.side_effect = Exception("Database error")

                with pytest.raises(ProductUpdateError) as exc_info:
                    await handler.handle(sample_command, CancellationToken())

                assert "Failed to update product in database" in str(exc_info.value)
                mock_session.rollback.assert_called_once()


class TestDeleteProductHandler:
    """Test DeleteProductHandler with comprehensive scenarios."""

    @pytest.fixture
    def handler(self):
        """Create handler instance."""
        return DeleteProductHandler()

    @pytest.fixture
    def sample_command(self):
        """Sample DeleteProductCommand for testing."""
        return DeleteProductCommand(product_id=uuid4())

    @pytest.fixture
    def mock_repository(self):
        """Mock ProductRepository."""
        return AsyncMock(spec=ProductRepository)

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_handle_success(self, handler, sample_command, mock_repository, mock_session):
        """Test successful product deletion."""
        with patch('app.modules.catalog.application.handlers.delete_product_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.delete_product_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                mock_repository.exists.return_value = True
                mock_repository.delete.return_value = True

                result = await handler.handle(sample_command, CancellationToken())

                assert isinstance(result, DeleteProductResult)
                assert result.is_success is True
                mock_repository.delete.assert_called_once_with(sample_command.product_id)
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_product_not_found(self, handler, sample_command, mock_repository, mock_session):
        """Test product deletion when product not found."""
        with patch('app.modules.catalog.application.handlers.delete_product_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.delete_product_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                mock_repository.exists.return_value = False

                with pytest.raises(ProductNotFoundError) as exc_info:
                    await handler.handle(sample_command, CancellationToken())

                assert str(sample_command.product_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_delete_failure(self, handler, sample_command, mock_repository, mock_session):
        """Test product deletion when delete operation fails."""
        with patch('app.modules.catalog.application.handlers.delete_product_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.delete_product_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                mock_repository.exists.return_value = True
                mock_repository.delete.return_value = False

                with pytest.raises(ProductDeleteError) as exc_info:
                    await handler.handle(sample_command, CancellationToken())

                assert "Failed to delete product from database" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_database_error(self, handler, sample_command, mock_repository, mock_session):
        """Test product deletion with database error."""
        with patch('app.modules.catalog.application.handlers.delete_product_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.delete_product_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                mock_repository.exists.return_value = True
                mock_repository.delete.side_effect = Exception("Database error")

                with pytest.raises(ProductDeleteError) as exc_info:
                    await handler.handle(sample_command, CancellationToken())

                assert "Failed to delete product from database" in str(exc_info.value)
                mock_session.rollback.assert_called_once()


class TestGetProductsHandler:
    """Test GetProductsHandler with comprehensive scenarios."""

    @pytest.fixture
    def handler(self):
        """Create handler instance."""
        return GetProductsHandler()

    @pytest.fixture
    def sample_products(self):
        """Sample products for testing."""
        from app.modules.catalog.domain.models import Product
        
        return [
            Product(
                id=uuid4(),
                name="Product 1",
                description="Description 1",
                price=Decimal("99.99"),
                image_file="image1.jpg",
                category=["Electronics"]
            ),
            Product(
                id=uuid4(),
                name="Product 2",
                description="Description 2",
                price=Decimal("149.99"),
                image_file="image2.jpg",
                category=["Gadgets"]
            )
        ]

    @pytest.fixture
    def mock_repository(self):
        """Mock ProductRepository."""
        return AsyncMock(spec=ProductRepository)

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_handle_success(self, handler, sample_products, mock_repository, mock_session):
        """Test successful products retrieval."""
        from app.modules.catalog.application.handlers.get_products_handler import GetProductsQuery
        from app.core.pagination.models import PaginatedResult

        query = GetProductsQuery(page=1, page_size=10)
        
        with patch('app.modules.catalog.application.handlers.get_products_handler.AsyncSessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            with patch('app.modules.catalog.application.handlers.get_products_handler.ProductRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repository
                
                # Mock repository methods
                mock_repository.get_all.return_value = (sample_products, 2)

                result = await handler.handle(query, CancellationToken())

                assert result is not None
                assert len(result.items) == 2
                assert result.total == 2
                assert result.page == 1
                assert result.size == 10
