# Enhanced REPR Pattern with CQRS Integration

## Overview

The Enhanced REPR (Request-Endpoint-Response-Pattern) implements a clean architectural flow that integrates with the CQRS (Command Query Responsibility Segregation) pattern. This provides a structured approach to handling HTTP requests through domain logic.

## Pattern Flow

```
HTTP Request → Command/Query → Result → HTTP Response
```

### 1. **Request** (HTTP Layer)
- HTTP request data is captured in Pydantic models
- Validation and serialization handled automatically
- Request models extend `BaseRequest` or `PaginatedRequest`

### 2. **Command/Query** (CQRS Layer)
- Requests are mapped to domain commands or queries
- Commands represent write operations (create, update, delete)
- Queries represent read operations (get, list, search)

### 3. **Result** (Domain Layer)
- Commands and queries return domain results
- Results contain business data and status information
- No HTTP concerns in this layer

### 4. **Response** (HTTP Layer)
- Domain results are mapped to HTTP responses
- Response models extend `BaseResponse`, `DataResponse`, or `PaginatedResponse`
- Standard success/error handling

## Key Components

### Base Classes

#### `BaseRequest`
Base class for HTTP request models:
```python
class GetProductRequest(BaseRequest):
    product_id: UUID = Field(..., description="Product ID to retrieve")
```

#### `BaseResponse`
Base class for HTTP response models:
```python
class BaseResponse(BaseModel):
    success: bool = Field(default=True)
    message: str = Field(default="")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

#### `DataResponse[T]`
Response containing data payload:
```python
class ProductResponse(DataResponse[ProductDto]):
    """HTTP response containing a single product."""
    pass
```

#### `PaginatedResponse[T]`
Response for paginated data:
```python
class ProductsResponse(PaginatedResponse[ProductDto]):
    """HTTP response containing multiple products with pagination."""
    pass
```

### CQRS Integration

#### `CQRSEndpoint`
Base endpoint that handles the full REPR flow:
```python
endpoint = CQRSEndpoint(
    request_mapper=RequestToQueryMapper(GetProductByIdQuery),
    result_mapper=ResultToDataResponseMapper(),
    mediator=mediator
)
```

#### `CommandEndpoint` & `QueryEndpoint`
Specialized endpoints for commands and queries:
```python
# For commands (write operations)
command_endpoint = CommandEndpoint(
    command_factory=CreateProductCommand,
    result_mapper=ResultToBaseResponseMapper(),
    mediator=mediator
)

# For queries (read operations)
query_endpoint = QueryEndpoint(
    query_factory=GetProductByIdQuery,
    result_mapper=ResultToDataResponseMapper(),
    mediator=mediator
)
```

### Mappers

#### `IRequestMapper`
Maps HTTP requests to commands/queries:
```python
class IRequestMapper(Generic[TRequest, CommandOrQuery], ABC):
    @abstractmethod
    async def map_to_command_or_query(self, request: TRequest, http_request: Request) -> CommandOrQuery:
        pass
```

#### `IResultMapper`
Maps command/query results to HTTP responses:
```python
class IResultMapper(Generic[TResult, TResponse], ABC):
    @abstractmethod
    async def map_to_response(self, result: TResult, original_request: Request) -> TResponse:
        pass
```

### Mediator Pattern

#### `IMediator`
Handles command and query execution:
```python
class IMediator(ABC):
    @abstractmethod
    async def send_command(self, command: ICommand[Any]) -> Any:
        pass
    
    @abstractmethod
    async def send_query(self, query: IQuery[Any]) -> Any:
        pass
```

## Usage Examples

### Simple Query Endpoint

```python
@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: UUID,
    request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory)
) -> ProductResponse:
    # 1. Create HTTP request model
    http_request = GetProductRequest(product_id=product_id)
    
    # 2. Create query endpoint
    endpoint = factory.create_query_endpoint(
        query_factory=GetProductByIdQuery,
        result_mapper=None  # Uses default DataResponse mapper
    )
    
    # 3. Execute REPR flow
    response = await endpoint.execute(request, http_request)
    
    return response
```

### Command Endpoint

```python
@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: CreateProductRequest,
    request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory)
) -> ProductResponse:
    # Create command endpoint
    endpoint = factory.create_command_endpoint(
        command_factory=CreateProductCommand,
        result_mapper=None  # Uses default response mapper
    )
    
    # Execute REPR flow
    response = await endpoint.execute(request, product_data)
    
    return response
```

### Paginated Query Endpoint

```python
@router.get("/", response_model=ProductsResponse)
async def get_products(
    page: int = 1,
    page_size: int = 10,
    request: Request = None,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory)
) -> ProductsResponse:
    # Create paginated request
    http_request = GetProductsRequest(page=page, page_size=page_size)
    
    # Create query endpoint with pagination mapper
    endpoint = factory.create_query_endpoint(
        query_factory=GetProductsQuery,
        result_mapper=PaginatedResultToResponseMapper[ProductDto]()
    )
    
    response = await endpoint.execute(request, http_request)
    return response
```

## Benefits

### 1. **Separation of Concerns**
- HTTP layer handles serialization/validation
- Domain layer handles business logic
- Clean boundaries between layers

### 2. **Testability**
- Each layer can be tested independently
- Easy to mock mediator for unit tests
- Clear contracts between components

### 3. **Consistency**
- Standardized request/response handling
- Common error handling patterns
- Uniform API structure

### 4. **Flexibility**
- Custom mappers for complex scenarios
- Pluggable mediator implementations
- Support for different response types

### 5. **CQRS Compliance**
- Clear command/query separation
- Proper result handling
- Domain-driven design principles

## Error Handling

The pattern includes comprehensive error handling:

```python
class CQRSErrorHandler:
    @staticmethod
    async def handle_error(error: Exception, request: Request) -> ErrorResponse:
        if isinstance(error, ValueError):
            return ErrorResponse(
                message="Invalid request data",
                error_code="VALIDATION_ERROR",
                details={"error": str(error)}
            )
        # ... other error types
```

## Factory Pattern

Use the `CQRSEndpointFactory` for consistent endpoint creation:

```python
def get_endpoint_factory(mediator: IMediator = Depends(get_mediator)) -> CQRSEndpointFactory:
    return CQRSEndpointFactory(mediator)

# In endpoints
factory = Depends(get_endpoint_factory)
endpoint = factory.create_query_endpoint(QueryClass, result_mapper)
```

## Best Practices

1. **Keep request/response models simple** - Focus on HTTP concerns only
2. **Use descriptive names** - Make the flow clear from naming
3. **Leverage type hints** - Enable better IDE support and validation
4. **Test each layer** - Unit test mappers, integration test endpoints
5. **Use factories** - Consistent endpoint creation and configuration
6. **Handle errors gracefully** - Provide meaningful error responses
7. **Document your contracts** - Clear API documentation for consumers 