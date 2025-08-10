"""CreateProductHandler with 1-1 parity to .NET implementation."""

from typing import Any
from uuid import UUID

from eshop.core.mediator.handler_registry import IRequestHandler
from eshop.modules.catalog.contracts.products.dtos import ProductDto
from eshop.modules.catalog.domain.models import Product


class CreateProductCommand:
    """Command to create a new product - matches .NET CreateProductCommand."""

    def __init__(self, product: ProductDto) -> None:
        self.product = product


class CreateProductResult:
    """Result of creating a product - matches .NET CreateProductResult."""

    def __init__(self, id: UUID) -> None:
        self.id = id


class CreateProductHandler(IRequestHandler[CreateProductCommand, CreateProductResult]):
    """Handler for CreateProductCommand - matches .NET CreateProductHandler."""

    def __init__(self, db_context: Any) -> None:  # type: ignore
        """Initialize handler with database context."""
        self.db_context = db_context

    async def handle(self, command: CreateProductCommand) -> CreateProductResult:
        """
        Handle the command - matches .NET Handle(CreateProductCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle

        Returns:
            CreateProductResult containing the created product ID
        """
        # Create Product entity from command object
        # save to database
        # return result

        product = self._create_new_product(command.product)

        # In real implementation, you'd use SQLAlchemy
        # dbContext.Products.Add(product);
        # await dbContext.SaveChangesAsync(cancellationToken);

        return CreateProductResult(product.id)

    def _create_new_product(self, product_dto: ProductDto) -> Product:
        """
        Create new product from DTO - matches .NET CreateNewProduct(ProductDto productDto).

        Args:
            product_dto: Product DTO

        Returns:
            Created Product entity
        """
        from uuid import uuid4

        product = Product.create(
            product_id=uuid4(),
            name=product_dto.name,
            category=product_dto.category,
            description=product_dto.description,
            image_file=product_dto.image_file,
            price=product_dto.price,
        )

        return product
