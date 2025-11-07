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
from app.modules.catalog.domain.exceptions import ProductNotFoundError
from app.modules.catalog.application.features.product.queries.get_products.query import (
    GetProductsQuery,
)
from app.modules.catalog.contracts.product.dtos import ProductDto
from app.modules.catalog.application.features.product.queries.get_product_by_id.query import (
    GetProductByIdQuery,
    GetProductByIdResult,
)
from app.modules.catalog.application.handlers.update_product_handler import (
    UpdateProductCommand,
)
from app.modules.catalog.application.handlers.delete_product_handler import (
    DeleteProductCommand,
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
    picture_url: str | None = Field(default=None, description="Product picture URL (optional)")
    category: list[str] = Field(..., description="Product categories")


class UpdateProductRequest(BaseRequest):
    """HTTP request for updating an existing product."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    picture_url: str | None = Field(default=None, description="Product picture URL (optional)")
    category: list[str] = Field(..., description="Product categories")


class DeleteProductRequest(BaseRequest):
    """HTTP request for deleting a product."""

    product_id: UUID = Field(..., description="Product ID to delete")


class GetProductsRequest(PaginatedRequest):
    """HTTP request for getting products with pagination."""

    category_id: UUID | None = Field(None, description="Filter by category ID")
    search_term: str | None = Field(None, description="Search term for product name")


# Response models (HTTP layer)
class ProductResponse(DataResponse[ProductDto]):
    """HTTP response containing a single product."""

    pass


class CreateProductResponse(BaseModel):
    """HTTP response for product creation."""

    id: UUID = Field(..., description="Created product ID")


class UpdateProductResponse(BaseModel):
    """HTTP response for product update."""

    success: bool = Field(..., description="Update operation success status")


class DeleteProductResponse(BaseModel):
    """HTTP response for product deletion."""

    success: bool = Field(..., description="Delete operation success status")


class ProductsResponse(PaginatedResponse[ProductDto]):
    """HTTP response containing multiple products with pagination."""

    pass


# Commands (CQRS layer - will be implemented)
class CreateProductCommand(ICommand[dict]):
    """Command to create a new product."""

    name: str
    description: str
    price: float
    picture_url: str | None = None  # Optional field
    category: list[str]


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
    # Create the query directly with the correct field name
    query = GetProductByIdQuery(id=product_id)

    # Create custom result mapper to extract product from GetProductByIdResult
    class GetProductByIdResultMapper:
        """Custom mapper to extract product from GetProductByIdResult."""
        
        async def map_to_response(self, result: GetProductByIdResult, original_request: Request) -> ProductResponse:
            """Map GetProductByIdResult to ProductResponse."""
            if result.product is None:
                raise ProductNotFoundError(product_id)
            return ProductResponse(data=result.product)

    # Create query endpoint using factory with custom mapper
    endpoint: Any = factory.create_query_endpoint(
        query_factory=GetProductByIdQuery,
        result_mapper=GetProductByIdResultMapper(),
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
    Create a new product.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles only)
    """
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=CreateProductCommand,
        result_mapper=None,  # Will use default response mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, request)

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


@router.put("/{product_id}", response_model=UpdateProductResponse)
async def update_product(
    product_id: UUID,
    request: UpdateProductRequest,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager only)
    _: Any = Depends(require_command_access()),
) -> UpdateProductResponse:
    """
    Update an existing product.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles only)
    """
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=UpdateProductCommand,
        result_mapper=None,  # Will use default response mapper
    )

    # Create the command with product ID and request data
    command = UpdateProductCommand(
        id=product_id,
        name=request.name,
        description=request.description,
        price=request.price,
        picture_url=request.picture_url,
        category=request.category,
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return UpdateProductResponse
    result = response.data  # This will be UpdateProductResult
    return UpdateProductResponse(success=result.is_success)


@router.delete("/{product_id}", response_model=DeleteProductResponse)
async def delete_product(
    product_id: UUID,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager only)
    _: Any = Depends(require_command_access()),
) -> DeleteProductResponse:
    """
    Delete a product.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles only)
    """
    # Extract user information from request for audit trail
    user_id = None
    user = getattr(http_request.state, "user", None)
    if user and hasattr(user, "sub"):
        try:
            user_id = UUID(user.sub)
        except (ValueError, AttributeError):
            pass  # Keep as None if user.sub is not a valid UUID
    
    # Create custom mapper that includes user context
    class DeleteProductCommandMapper:
        """Custom mapper that adds user context to delete command."""
        
        async def map_to_command_or_query(
            self, request: DeleteProductRequest, http_request: Request
        ) -> DeleteProductCommand:
            """Map HTTP request to delete command with user context."""
            user_id = None
            user = getattr(http_request.state, "user", None)
            if user and hasattr(user, "sub"):
                try:
                    user_id = UUID(user.sub)
                except (ValueError, AttributeError):
                    pass
            
            return DeleteProductCommand(
                product_id=request.product_id,
                deleted_by=user_id,
                deletion_reason=None  # Can be extended to accept from request body
            )
    
    # Create command endpoint using factory with custom mapper
    endpoint: Any = factory.create_command_endpoint(
        command_factory=DeleteProductCommand,
        result_mapper=None,  # Will use default response mapper
    )
    
    # Override the request mapper with our custom one
    endpoint.request_mapper = DeleteProductCommandMapper()

    # Create the HTTP request model (though we'll use the mapper)
    request_model = DeleteProductRequest(product_id=product_id)

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, request_model)

    # Extract the result and return DeleteProductResponse
    result = response.data  # This will be DeleteProductResult
    return DeleteProductResponse(success=result.is_success)


# Admin endpoints for managing deleted products
@router.get("/admin/deleted", response_model=ProductsResponse)
async def get_deleted_products(
    http_request: Request,
    page: int = 1,
    page_size: int = 10,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Admin only access
    _: Any = Depends(require_command_access()),
) -> ProductsResponse:
    """
    Get deleted products (admin only).
    
    RBAC: Requires command access (admin only)
    """
    # Use direct repository access for admin operations
    from app.core.database.session import AsyncSessionLocal
    from app.modules.catalog.infrastructure.persistence.repositories.product_repository import ProductRepositoryImpl
    
    async with AsyncSessionLocal() as session:
        repository = ProductRepositoryImpl(session)
        products, total_count = await repository.get_deleted_products(page, page_size)
        
        # Convert to DTOs
        from app.modules.catalog.application.mappers.product_mapper import ProductMapper
        product_dtos = [ProductMapper.to_dto(product) for product in products]
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return ProductsResponse(
            data=product_dtos,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_count=total_count,
        )


@router.post("/admin/restore/{product_id}", response_model=DeleteProductResponse)
async def restore_product(
    product_id: UUID,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Admin only access
    _: Any = Depends(require_command_access()),
) -> DeleteProductResponse:
    """
    Restore a deleted product (admin only).
    
    RBAC: Requires command access (admin only)
    """
    # Extract user information from request
    user_id = None
    user = getattr(http_request.state, "user", None)
    if user and hasattr(user, "sub"):
        try:
            user_id = UUID(user.sub)
        except (ValueError, AttributeError):
            pass
    
    # Use direct repository access for admin operations
    from app.core.database.session import AsyncSessionLocal
    from app.modules.catalog.infrastructure.persistence.repositories.product_repository import ProductRepositoryImpl
    from app.modules.catalog.domain.exceptions import ProductNotFoundError
    
    async with AsyncSessionLocal() as session:
        repository = ProductRepositoryImpl(session)
        
        # Check if product exists and is deleted
        deleted_product = await repository.get_deleted_by_id(product_id)
        if not deleted_product:
            raise ProductNotFoundError(product_id)
        
        success = await repository.restore_product(product_id, restored_by=user_id)
        await session.commit()
        
        if success:
            # Invalidate cache
            from app.modules.catalog.infrastructure.cache_service import CatalogCacheService, RedisCacheService
            cache_service = CatalogCacheService(RedisCacheService())
            await cache_service.invalidate_product(product_id)
            await cache_service.invalidate_products_list()
        
        return DeleteProductResponse(success=success)
