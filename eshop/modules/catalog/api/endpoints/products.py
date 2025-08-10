"""Product endpoints demonstrating enhanced REPR pattern with CQRS."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import Field

from eshop.core.contracts.cqrs import ICommand, IQuery
from eshop.core.mediator.fastapi_integration import get_mediator_dependency
from eshop.core.repr.base import (
    BaseRequest,
    CQRSEndpointFactory,
    DataResponse,
    IMediator,
    PaginatedRequest,
    PaginatedResponse,
)
from eshop.modules.catalog.contracts.products.dtos import ProductDto
from eshop.modules.catalog.contracts.products.features.get_product_by_id import (
    GetProductByIdQuery,
)

router = APIRouter(prefix="/products", tags=["products"])


# Request models (HTTP layer)
class GetProductRequest(BaseRequest):
    """HTTP request for getting a product by ID."""

    product_id: UUID = Field(..., description="Product ID to retrieve")


class CreateProductRequest(BaseRequest):
    """HTTP request for creating a new product."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    picture_url: str = Field(..., description="Product picture URL")


class GetProductsRequest(PaginatedRequest):
    """HTTP request for getting products with pagination."""

    category_id: UUID | None = Field(None, description="Filter by category ID")
    search_term: str | None = Field(None, description="Search term for product name")


# Response models (HTTP layer)
class ProductResponse(DataResponse[ProductDto]):
    """HTTP response containing a single product."""

    pass


class ProductsResponse(PaginatedResponse[ProductDto]):
    """HTTP response containing multiple products with pagination."""

    pass


# Commands (CQRS layer - will be implemented)
class CreateProductCommand(ICommand[dict]):
    """Command to create a new product."""

    name: str
    description: str
    price: float
    picture_url: str


# Queries (CQRS layer - already have GetProductByIdQuery)
class GetProductsQuery(IQuery[dict]):
    """Query to get products with optional filtering and pagination."""

    page: int = 1
    page_size: int = 10
    category_id: UUID | None = None
    search_term: str | None = None


# Dependency for mediator - matches .NET ISender dependency injection
def get_mediator() -> IMediator:
    """Get mediator instance - matches .NET ISender dependency injection."""
    return get_mediator_dependency()


# Dependency for CQRS endpoint factory
def get_endpoint_factory(
    mediator: IMediator = Depends(get_mediator),
) -> CQRSEndpointFactory:
    """Get CQRS endpoint factory."""
    return CQRSEndpointFactory(mediator)


# Endpoints demonstrating the REPR pattern: Request -> Command/Query -> Result -> Response


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: UUID,
    request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
) -> ProductResponse:
    """
    Get a product by ID.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response
    """
    # Create the HTTP request model
    http_request = GetProductRequest(product_id=product_id)

    # Create query endpoint using factory
    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetProductByIdQuery,
        result_mapper=None,  # Will use default DataResponse mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(request, http_request)

    return response  # type: ignore


@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: CreateProductRequest,
    request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
) -> ProductResponse:
    """
    Create a new product.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    """
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=CreateProductCommand,
        result_mapper=None,  # Will use default response mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(request, product_data)

    return response  # type: ignore


@router.get("/", response_model=ProductsResponse)
async def get_products(
    request: Request,
    page: int = 1,
    page_size: int = 10,
    category_id: UUID | None = None,
    search_term: str | None = None,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
) -> ProductsResponse:
    """
    Get products with pagination and filtering.

    Demonstrates: HTTP Request -> Query -> Result -> HTTP Response (with pagination)
    """
    # Create the HTTP request model
    http_request = GetProductsRequest(
        page=page, page_size=page_size, category_id=category_id, search_term=search_term
    )

    # Create query endpoint with custom pagination mapper
    from eshop.core.repr.base import PaginatedResultToResponseMapper

    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetProductsQuery,
        result_mapper=PaginatedResultToResponseMapper[ProductDto](),
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(request, http_request)

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
