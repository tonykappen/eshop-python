"""Product endpoints demonstrating enhanced REPR pattern with CQRS and RBAC."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.auth.rbac import require_command_access, require_query_access
from app.core.contracts.cqrs import ICommand
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.fastapi_integration import (
    get_cancellation_token_dependency,
    get_mediator_dependency,
)
from app.core.repr.base import (
    BaseRequest,
    CQRSEndpointFactory,
    DataResponse,
    IMediator,
    PaginatedRequest,
    PaginatedResponse,
)
from app.modules.catalog.application.handlers.get_products_handler import (
    GetProductsQuery,
)
from app.modules.catalog.contracts.products.dtos import ProductDto
from app.modules.catalog.contracts.products.features.get_product_by_id import (
    GetProductByIdQuery,
)

router = APIRouter(prefix="/products", tags=["products"])


# Request models (HTTP layer)
class GetProductRequest(BaseRequest):
    """HTTP request for getting a product by ID."""

    product_id: UUID = Field(..., description="Product ID to retrieve")


class CreateProductRequest(BaseRequest):
    """HTTP request for creating a new product - matches .NET CreateProductRequest."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    picture_url: str = Field(..., description="Product picture URL")
    category: list[str] = Field(..., description="Product categories")


class UpdateProductRequest(BaseRequest):
    """HTTP request for updating an existing product."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    picture_url: str = Field(..., description="Product picture URL")
    category: list[str] = Field(..., description="Product categories")


class GetProductsRequest(PaginatedRequest):
    """HTTP request for getting products with pagination."""

    category_id: UUID | None = Field(None, description="Filter by category ID")
    search_term: str | None = Field(None, description="Search term for product name")


# Response models (HTTP layer)
class ProductResponse(DataResponse[ProductDto]):
    """HTTP response containing a single product."""

    pass


class CreateProductResponse(BaseModel):
    """HTTP response for product creation - matches .NET CreateProductResponse."""

    id: UUID = Field(..., description="Created product ID")


class ProductsResponse(PaginatedResponse[ProductDto]):
    """HTTP response containing multiple products with pagination."""

    pass


# Commands (CQRS layer - will be implemented)
# Import the actual command from the handler
from app.modules.catalog.application.handlers.create_product_handler import CreateProductCommand


# Import the actual commands from the handlers
from app.modules.catalog.application.handlers.update_product_handler import UpdateProductCommand
from app.modules.catalog.application.handlers.delete_product_handler import DeleteProductCommand


# Dependency for mediator - matches .NET ISender dependency injection
def get_mediator() -> IMediator:
    """Get mediator instance - matches .NET ISender dependency injection."""
    return get_mediator_dependency()


# Dependency for cancellation token - matches .NET CancellationToken dependency injection
def get_cancellation_token(request: Request) -> CancellationToken:
    """Get cancellation token from request - matches .NET CancellationToken injection."""
    return get_cancellation_token_dependency(request)


# Dependency for CQRS endpoint factory
def get_endpoint_factory(
    mediator: IMediator = Depends(get_mediator),
) -> CQRSEndpointFactory:
    """Get CQRS endpoint factory."""
    return CQRSEndpointFactory(mediator)


# Endpoints demonstrating the REPR pattern: Request -> Command/Query -> Result -> Response
# with RBAC protection


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: UUID,
    request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Query access required (admin, manager, user)
    _: Any = Depends(require_query_access()),
) -> ProductResponse:
    """
    Get a product by ID.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response
    RBAC: Requires query access (admin, manager, user roles)
    """
    # Create the query directly
    query = GetProductByIdQuery(id=product_id)

    # Create query endpoint using factory
    endpoint: Any = factory.create_query_endpoint(
        query_factory=lambda: query,
        result_mapper=None,  # Will use default DataResponse mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(request, query)

    return response  # type: ignore


@router.post("/", response_model=CreateProductResponse, status_code=201)
async def create_product(
    request: CreateProductRequest,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager only)
    _: Any = Depends(require_command_access()),
) -> CreateProductResponse:
    """
    Create a new product - matches .NET CreateProductEndpoint.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles only)
    """
    # Create ProductDto from request
    from app.modules.catalog.contracts.products.dtos import ProductDto
    from decimal import Decimal
    
    product_dto = ProductDto(
        name=request.name,
        description=request.description,
        price=Decimal(str(request.price)),
        picture_url=request.picture_url,
        category=request.category
    )
    
    # Create command with the product DTO
    command = CreateProductCommand(product=product_dto)
    
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=lambda: command,
        result_mapper=None,  # Will use default response mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return CreateProductResponse
    result = response.data  # This will be CreateProductResult
    return CreateProductResponse(id=result.id)


@router.get("/", response_model=ProductsResponse)
async def get_products(
    http_request: Request,
    page: int = 1,
    page_size: int = 10,
    category_id: UUID | None = None,
    search_term: str | None = None,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Query access required (admin, manager, user)
    _: Any = Depends(require_query_access()),
) -> ProductsResponse:
    """
    Get products with pagination and filtering.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response (with pagination)
    RBAC: Requires query access (admin, manager, user roles)
    """
    # Create the HTTP request model
    request = GetProductsRequest(
        page=page, page_size=page_size, category_id=category_id, search_term=search_term
    )

    # Create query endpoint with custom pagination mapper
    from app.core.repr.base import PaginatedResultToResponseMapper

    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetProductsQuery,
        result_mapper=PaginatedResultToResponseMapper[ProductDto](),
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, request)

    return response  # type: ignore


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    request: UpdateProductRequest,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager only)
    _: Any = Depends(require_command_access()),
) -> ProductResponse:
    """
    Update an existing product.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles only)
    """
    # Create the command with the product_id from the path
    from app.modules.catalog.application.handlers.update_product_handler import UpdateProductCommand
    command = UpdateProductCommand(
        id=product_id,
        name=request.name,
        description=request.description,
        price=request.price,
        picture_url=request.picture_url,
        category=request.category
    )

    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=lambda: command,
        result_mapper=None,  # Will use default response mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    return response  # type: ignore


@router.delete("/{product_id}", response_model=dict)
async def delete_product(
    product_id: UUID,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin only)
    _: Any = Depends(require_command_access()),
) -> dict:
    """
    Delete a product.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin role only)
    """
    # Create the command with the product_id from the path
    from app.modules.catalog.application.handlers.delete_product_handler import DeleteProductCommand
    command = DeleteProductCommand(product_id=product_id)

    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=lambda: command,
        result_mapper=None,  # Will use default response mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    return response  # type: ignore


# Example of custom request mapper (advanced usage)
class CustomGetProductRequestMapper:
    """Custom mapper that adds request context to queries."""

    async def map_to_command_or_query(
        self, request: GetProductRequest, http_request: Request
    ) -> GetProductByIdQuery:
        """Map HTTP request to query with additional context."""
        # Could add user context, tracing, etc.
        user_id = http_request.headers.get("X-User-ID")

        # Create the query
        query = GetProductByIdQuery(id=request.product_id)

        # Add context if needed (this is just an example)
        if user_id:
            # In a real implementation, you might set audit context
            pass

        return query


# Test endpoint without authentication for debugging
@router.post("/test-create", response_model=CreateProductResponse, status_code=201)
async def test_create_product(
    request: CreateProductRequest,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
) -> CreateProductResponse:
    """
    Test endpoint for creating a product without authentication.
    """
    # Create ProductDto from request
    from app.modules.catalog.contracts.products.dtos import ProductDto
    from decimal import Decimal
    
    product_dto = ProductDto(
        name=request.name,
        description=request.description,
        price=Decimal(str(request.price)),
        picture_url=request.picture_url,
        category=request.category
    )
    
    # Create command with the product DTO
    command = CreateProductCommand(product=product_dto)
    
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=lambda: command,
        result_mapper=None,  # Will use default response mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return CreateProductResponse
    result = response.data  # This will be CreateProductResult
    return CreateProductResponse(id=result.id)
