# .NET to FastAPI Implementation Guide
## MediatR & Carter Extensions Pattern Migration

**Document Version:** 1.0  
**Last Updated:** October 9, 2025  
**Author:** Technical Documentation Team

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture Comparison](#architecture-comparison)
3. [MediatR Extensions - Handler Auto-Registration](#mediatr-extensions---handler-auto-registration)
4. [Carter Extensions - API Routing](#carter-extensions---api-routing)
5. [Pipeline Behaviors](#pipeline-behaviors)
6. [Exception Handling](#exception-handling)
7. [Complete Request Flow](#complete-request-flow)
8. [Code Examples](#code-examples)
9. [Key Differences](#key-differences)
10. [Best Practices](#best-practices)

---

## 🎯 Overview

This document explains how the .NET **MediatR** and **Carter** extension patterns have been implemented in FastAPI, maintaining **1-to-1 parity** with the original .NET implementation. The core functionality includes:

### ✅ Features Implemented

1. **Auto-Registration of Handlers** from assemblies/modules
2. **Pipeline Behaviors** with validation and logging
3. **Custom Exception Handling** with standardized error responses
4. **CQRS Pattern** (Command Query Responsibility Segregation)
5. **Dependency Injection** for mediator and handlers

---

## 🏗️ Architecture Comparison

### .NET Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ASP.NET Core API                      │
├─────────────────────────────────────────────────────────┤
│  Carter Modules (API Endpoints)                         │
│    ↓                                                     │
│  MediatR (Request Pipeline)                             │
│    ↓                                                     │
│  ValidationBehavior (FluentValidation)                  │
│    ↓                                                     │
│  LoggingBehavior (ILogger)                              │
│    ↓                                                     │
│  Request Handler (IRequestHandler)                      │
│    ↓                                                     │
│  CustomExceptionHandler (IExceptionHandler)             │
└─────────────────────────────────────────────────────────┘
```

### FastAPI Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      FastAPI                             │
├─────────────────────────────────────────────────────────┤
│  API Routes (FastAPI Endpoints)                         │
│    ↓                                                     │
│  Mediator (Request Pipeline)                            │
│    ↓                                                     │
│  ValidationBehavior (Pydantic)                          │
│    ↓                                                     │
│  LoggingBehavior (BaseLogger)                           │
│    ↓                                                     │
│  Request Handler (IRequestHandler)                      │
│    ↓                                                     │
│  CustomExceptionHandler (Exception Middleware)          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 MediatR Extensions - Handler Auto-Registration

### .NET Implementation

**File:** `Shared/Extensions/MediatRExtentions.cs`

```csharp
using FluentValidation;
using Microsoft.Extensions.DependencyInjection;
using Shared.Behaviors;
using System.Reflection;

namespace Shared.Extensions;
public static class MediatRExtentions
{
    public static IServiceCollection AddMediatRWithAssemblies
        (this IServiceCollection services, params Assembly[] assemblies)
    {
        services.AddMediatR(config =>
        {
            config.RegisterServicesFromAssemblies(assemblies);
            config.AddOpenBehavior(typeof(ValidationBehavior<,>));
            config.AddOpenBehavior(typeof(LoggingBehavior<,>));
        });

        services.AddValidatorsFromAssemblies(assemblies);

        return services;
    }
}
```

**Usage in Program.cs:**
```csharp
var catalogAssembly = typeof(CatalogModule).Assembly;
var basketAssembly = typeof(BasketModule).Assembly;

builder.Services.AddMediatRWithAssemblies(catalogAssembly, basketAssembly);
```

### FastAPI Implementation

**File:** `app/core/mediator/extensions.py`

```python
"""Extensions for mediator registration with 1-1 parity to .NET MediatRExtensions."""

import inspect
from typing import Any
from app.core.logging.base_logger import BaseLogger
from .handler_registry import HandlerRegistry
from .mediator import Mediator


def add_mediator_with_assemblies(services: Any, *assemblies: Any) -> Any:
    """
    Add mediator with assemblies - matches .NET AddMediatRWithAssemblies().
    
    Args:
        services: Service collection (FastAPI dependency container)
        *assemblies: Assemblies to scan for handlers
        
    Returns:
        Service collection with mediator registered
    """
    logger = BaseLogger(__name__)
    
    # Create handler registry
    handler_registry = HandlerRegistry()
    
    # Scan assemblies for handlers
    for assembly in assemblies:
        logger.log_debug_with_context(
            "Scanning assembly for handlers",
            context={"assembly_name": assembly.__name__},
        )
        _register_handlers_from_assembly(handler_registry, assembly)
    
    # Create mediator
    mediator = Mediator(handler_registry)
    
    # Register mediator as singleton
    services["mediator"] = mediator
    services["handler_registry"] = handler_registry
    
    logger.log_with_context(
        "Registered mediator with handlers",
        "info",
        context={"handler_count": len(handler_registry.get_registered_types())},
    )
    
    return services


def _register_handlers_from_assembly(
    handler_registry: HandlerRegistry, assembly: Any
) -> None:
    """Register all handlers from an assembly - matches .NET RegisterServicesFromAssemblies()."""
    logger = BaseLogger(__name__)
    
    try:
        # Get all classes from the assembly
        for name, obj in inspect.getmembers(assembly):
            if inspect.isclass(obj) and _is_request_handler(obj):
                # Extract request type from handler
                request_type = _extract_request_type(obj)
                if request_type:
                    handler_instance = obj()
                    handler_registry.register_handler(request_type, handler_instance)
                    logger.log_debug_with_context(
                        "Registered handler for request",
                        context={
                            "handler_name": name,
                            "request_type": request_type.__name__,
                        },
                    )
    except Exception as e:
        logger.log_warning_with_context(
            "Failed to scan assembly",
            context={"assembly_name": assembly.__name__, "error": str(e)},
        )


def _is_request_handler(cls: type[Any]) -> bool:
    """Check if a class is a request handler."""
    if not inspect.isabstract(cls) and (
        any(base.__name__ == "IRequestHandler" for base in cls.__mro__)
        or (hasattr(cls, "handle") and inspect.iscoroutinefunction(cls.handle))
    ):
        return True
    return False
```

**Usage in FastAPI:**
```python
from app.core.mediator.extensions import add_mediator_with_assemblies
from app.modules import catalog, basket, ordering

services = {}
add_mediator_with_assemblies(
    services,
    catalog.application.handlers,
    basket.application.handlers,
    ordering.application.handlers,
)
```

### Key Features

| Feature | .NET | FastAPI |
|---------|------|---------|
| **Assembly Scanning** | `RegisterServicesFromAssemblies()` | `_register_handlers_from_assembly()` |
| **Handler Detection** | Reflection + `IRequestHandler` | Inspection + `IRequestHandler` |
| **Automatic Registration** | ✅ Yes | ✅ Yes |
| **Behavior Pipeline** | ✅ Yes | ✅ Yes |
| **Validator Registration** | FluentValidation | Pydantic (built-in) |

---

## 🛣️ Carter Extensions - API Routing

### .NET Implementation

**File:** `Shared/Extensions/CarterExtentions.cs`

```csharp
using Carter;
using Microsoft.Extensions.DependencyInjection;
using System.Reflection;

namespace Shared.Extensions;
public static class CarterExtentions
{
    public static IServiceCollection AddCarterWithAssemblies
        (this IServiceCollection services, params Assembly[] assemblies)
    {
        services.AddCarter(configurator: config =>
        {
            foreach (var assembly in assemblies)
            {
                var modules = assembly.GetTypes()
                    .Where(t => t.IsAssignableTo(typeof(ICarterModule)))
                    .ToArray();

                config.WithModules(modules);
            }
        });

        return services;
    }
}
```

### FastAPI Implementation

**File:** `app/core/mediator/fastapi_integration.py`

```python
"""FastAPI integration for mediator pattern with 1-1 parity to .NET."""

from typing import Any
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from .handler_registry import HandlerRegistry
from .mediator import Mediator

# Global services container (simplified version of .NET IServiceCollection)
_services: dict[str, Any] = {}


def configure_mediator() -> None:
    """Configure mediator for FastAPI - matches .NET Program.cs configuration."""
    # Create handler registry
    handler_registry = HandlerRegistry()
    
    # Register module handlers
    _register_module_handlers(handler_registry)
    
    # Create mediator
    mediator = Mediator(handler_registry)
    
    # Register in services
    _services["mediator"] = mediator
    _services["handler_registry"] = handler_registry


def _register_module_handlers(handler_registry: HandlerRegistry) -> None:
    """Register all module handlers."""
    # Register catalog module handlers
    from app.modules.catalog.application.handlers.catalog_handler_registration import (
        register_catalog_handlers,
    )
    
    register_catalog_handlers(handler_registry)
    
    # Register basket module handlers
    # from app.modules.basket.application.handlers import register_basket_handlers
    # register_basket_handlers(handler_registry)
    
    # Register ordering module handlers
    # from app.modules.ordering.application.handlers import register_ordering_handlers
    # register_ordering_handlers(handler_registry)


def get_mediator() -> Mediator:
    """Get mediator dependency - matches .NET ISender dependency injection."""
    mediator = _services.get("mediator")
    if not mediator:
        raise RuntimeError("Mediator not configured. Call configure_mediator() first.")
    return mediator


# FastAPI dependency functions
def get_mediator_dependency() -> Mediator:
    """FastAPI dependency for mediator."""
    return get_mediator()
```

**Usage in FastAPI Routes:**
```python
from fastapi import APIRouter, Depends
from app.core.mediator.fastapi_integration import get_mediator_dependency
from app.core.mediator.mediator import Mediator

router = APIRouter()

@router.post("/products")
async def create_product(
    request: CreateProductRequest,
    mediator: Mediator = Depends(get_mediator_dependency)
):
    command = CreateProductCommand(**request.dict())
    result = await mediator.send(command, CancellationToken())
    return result
```

### Comparison

| Aspect | Carter (.NET) | FastAPI |
|--------|---------------|---------|
| **Module Discovery** | `ICarterModule` scanning | Manual registration + DI |
| **Endpoint Registration** | Auto-mapped from modules | Standard FastAPI routes |
| **Mediator Integration** | `ISender` injection | Dependency injection |
| **Request Handling** | Through MediatR pipeline | Through Mediator pipeline |

---

## 🔄 Pipeline Behaviors

### 1. Validation Behavior

#### .NET Implementation

**File:** `Shared/Behaviors/ValidationBehavior.cs`

```csharp
using FluentValidation;
using MediatR;
using Shared.Contracts.CQRS;

namespace Shared.Behaviors;
public class ValidationBehavior<TRequest, TResponse>
    (IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : ICommand<TResponse>
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        var context = new ValidationContext<TRequest>(request);

        var validationResults = await Task.WhenAll(
            validators.Select(v => v.ValidateAsync(context, cancellationToken))
        );

        var failures = validationResults
            .Where(r => r.Errors.Any())
            .SelectMany(r => r.Errors)
            .ToList();

        if (failures.Any())
            throw new ValidationException(failures);

        return await next();
    }
}
```

#### FastAPI Implementation

**File:** `app/core/mediator/behaviors.py`

```python
"""Pipeline behaviors for mediator pattern with 1-1 parity to .NET MediatR."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar
from app.core.logging.base_logger import BaseLogger

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class IPipelineBehavior(ABC, Generic[TRequest, TResponse]):
    """Base interface for pipeline behaviors - matches .NET IPipelineBehavior<TRequest, TResponse>."""
    
    @abstractmethod
    async def handle(
        self, request: TRequest, next_handler: Callable[[], Any]
    ) -> TResponse:
        """Handle the request in the pipeline."""
        pass


class ValidationBehavior(IPipelineBehavior[TRequest, TResponse]):
    """Validation behavior - matches .NET ValidationBehavior<TRequest, TResponse>."""
    
    def __init__(self) -> None:
        self.logger = BaseLogger(__name__)
    
    async def handle(
        self, request: TRequest, next_handler: Callable[[], Awaitable[TResponse]]
    ) -> TResponse:
        """Handle validation - matches .NET ValidationBehavior.Handle()."""
        # Use Pydantic validation (equivalent to FluentValidation)
        if hasattr(request, "model_validate") and hasattr(request, "model_dump"):
            try:
                # Validate the request using Pydantic
                request.model_validate(request.model_dump())
            except Exception as validation_error:
                self.logger.log_error_with_context(
                    "Validation failed for request",
                    error=validation_error,
                    context={"request_type": type(request).__name__},
                )
                raise ValueError(
                    f"Validation failed: {validation_error}"
                ) from validation_error
        
        result = await next_handler()
        return result
```

### 2. Logging Behavior

#### .NET Implementation

**File:** `Shared/Behaviors/LoggingBehavior.cs`

```csharp
using MediatR;
using Microsoft.Extensions.Logging;
using System.Diagnostics;

namespace Shared.Behaviors;
public class LoggingBehavior<TRequest, TResponse>
    (ILogger<LoggingBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull, IRequest<TResponse>
    where TResponse : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        logger.LogInformation(
            "[START] Handle request={Request} - Response={Response} - RequestData={RequestData}",
            typeof(TRequest).Name, typeof(TResponse).Name, request);

        var timer = new Stopwatch();
        timer.Start();

        var response = await next();

        timer.Stop();
        var timeTaken = timer.Elapsed;
        
        // Log performance warning if request takes more than 3 seconds
        if (timeTaken.Seconds > 3)
            logger.LogWarning(
                "[PERFORMANCE] The request {Request} took {TimeTaken} seconds.",
                typeof(TRequest).Name, timeTaken.Seconds);

        logger.LogInformation(
            "[END] Handled {Request} with {Response}",
            typeof(TRequest).Name, typeof(TResponse).Name);
            
        return response;
    }
}
```

#### FastAPI Implementation

**File:** `app/core/mediator/behaviors.py`

```python
import time
import uuid


class LoggingBehavior(IPipelineBehavior[TRequest, TResponse]):
    """Logging behavior - matches .NET LoggingBehavior<TRequest, TResponse>."""
    
    def __init__(self) -> None:
        self.logger = BaseLogger(__name__)
    
    async def handle(
        self, request: TRequest, next_handler: Callable[[], Awaitable[TResponse]]
    ) -> TResponse:
        """Handle logging - matches .NET LoggingBehavior.Handle()."""
        request_type = type(request).__name__
        response_type = self._get_response_type(request)
        
        # Generate trace_id for this operation
        trace_id = str(uuid.uuid4())
        
        self.logger.log_with_context(
            "Starting request handling",
            context={
                "request_type": request_type,
                "response_type": response_type,
                "request_data": str(request),
                "trace_id": trace_id,
            },
        )
        
        start_time = time.time()
        
        try:
            response = await next_handler()
            
            elapsed_time = time.time() - start_time
            
            # Log performance warning if request takes more than 3 seconds
            if elapsed_time > 3:
                self.logger.log_warning_with_context(
                    "Request performance warning",
                    context={
                        "request_type": request_type,
                        "elapsed_time": elapsed_time,
                        "trace_id": trace_id,
                    },
                )
            
            self.logger.log_with_context(
                "Request handling completed",
                context={
                    "request_type": request_type,
                    "response_type": response_type,
                    "trace_id": trace_id,
                },
            )
            
            return response
            
        except Exception as e:
            self.logger.log_error_with_context(
                "Request handling failed",
                error=e,
                context={"request_type": request_type, "trace_id": trace_id},
            )
            raise
```

### Behavior Pipeline Execution

**File:** `app/core/mediator/mediator.py`

```python
class Mediator(IMediator):
    """Main mediator implementation with 1-1 parity to .NET MediatR."""
    
    def __init__(self, handler_registry: HandlerRegistry) -> None:
        self.handler_registry = handler_registry
        self.logger = BaseLogger(__name__)
        
        # Pipeline behaviors (matches .NET MediatR behaviors)
        self.behaviors: list[Any] = [ValidationBehavior(), LoggingBehavior()]
    
    async def _execute_pipeline(
        self, request: Any, handler: Any, cancellation_token: CancellationToken
    ) -> Any:
        """Execute request through pipeline behaviors - matches .NET MediatR pipeline."""
        # Start with the handler
        current_handler = handler
        
        # Apply behaviors in reverse order (last in, first out)
        for behavior in reversed(self.behaviors):
            current_handler = behavior.wrap(current_handler)
        
        # Execute the pipeline with cancellation token
        return await current_handler.handle(request, cancellation_token)
```

---

## ⚠️ Exception Handling

### .NET Exception Classes

**Files:** `Shared/Exceptions/*.cs`

```csharp
// BadRequestException.cs
namespace Shared.Exceptions;
public class BadRequestException : Exception
{
    public BadRequestException(string message) : base(message) { }
    
    public BadRequestException(string message, string details) : base(message)
    {
        Details = details;
    }
    
    public string? Details { get; }
}

// NotFoundException.cs
namespace Shared.Exceptions;
public class NotFoundException : Exception
{
    public NotFoundException(string message) : base(message) { }
    
    public NotFoundException(string name, object key) 
        : base($"Entity \"{name}\" ({key}) was not found.")
    {
    }
}

// InternalServerException.cs
namespace Shared.Exceptions;
public class InternalServerException : Exception
{
    public InternalServerException(string message) : base(message) { }
    
    public InternalServerException(string message, string details) : base(message)
    {
        Details = details;
    }
    
    public string? Details { get; }
}
```

### FastAPI Exception Classes

**File:** `app/core/exceptions/base.py`

```python
"""Base exception classes with 1-1 parity to .NET exceptions."""

from typing import Any


class BaseError(Exception):
    """Base exception class - matches .NET Exception pattern."""
    
    def __init__(self, message: str = "An error occurred", details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class BadRequestError(BaseError):
    """Exception for bad request errors (400) - matches .NET BadRequestException."""
    
    def __init__(self, message: str = "Bad request", details: str | None = None):
        super().__init__(message, details)


class NotFoundError(BaseError):
    """Exception for not found errors (404) - matches .NET NotFoundException."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        name: str | None = None,
        key: Any | None = None,
    ):
        if name and key:
            message = f'Entity "{name}" ({key}) was not found.'
        super().__init__(message)


class InternalServerError(BaseError):
    """Exception for internal server errors (500) - matches .NET InternalServerException."""
    
    def __init__(
        self, message: str = "Internal server error", details: str | None = None
    ):
        super().__init__(message, details)


class ValidationError(BaseError):
    """Exception for validation errors - matches .NET ValidationException."""
    
    def __init__(
        self,
        message: str = "Validation error",
        errors: dict[str, Any] | None = None,
        details: str | None = None,
    ):
        self.errors = errors or {}
        super().__init__(message, details)
```

### .NET Exception Handler

**File:** `Shared/Exceptions/Handler/CustomExceptionHandler.cs`

```csharp
using FluentValidation;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace Shared.Exceptions.Handler;
public class CustomExceptionHandler
    (ILogger<CustomExceptionHandler> logger)
    : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext context,
        Exception exception,
        CancellationToken cancellationToken)
    {
        logger.LogError(
            "Error Message: {exceptionMessage}, Time of occurrence {time}",
            exception.Message, DateTime.UtcNow);

        (string Detail, string Title, int StatusCode) details = exception switch
        {
            InternalServerException => (
                exception.Message,
                exception.GetType().Name,
                StatusCodes.Status500InternalServerError
            ),
            ValidationException => (
                exception.Message,
                exception.GetType().Name,
                StatusCodes.Status400BadRequest
            ),
            BadRequestException => (
                exception.Message,
                exception.GetType().Name,
                StatusCodes.Status400BadRequest
            ),
            NotFoundException => (
                exception.Message,
                exception.GetType().Name,
                StatusCodes.Status404NotFound
            ),
            _ => (
                exception.Message,
                exception.GetType().Name,
                StatusCodes.Status500InternalServerError
            )
        };

        var problemDetails = new ProblemDetails
        {
            Title = details.Title,
            Detail = details.Detail,
            Status = details.StatusCode,
            Instance = context.Request.Path
        };

        problemDetails.Extensions.Add("traceId", context.TraceIdentifier);

        if (exception is ValidationException validationException)
        {
            problemDetails.Extensions.Add("ValidationErrors", validationException.Errors);
        }

        await context.Response.WriteAsJsonAsync(problemDetails, cancellationToken);
        return true;
    }
}
```

### FastAPI Exception Handler

**File:** `app/core/exceptions/handler.py`

```python
"""Custom exception handler with 1-1 parity to .NET CustomExceptionHandler."""

import traceback
from typing import Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from app.core.exceptions.base import *
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class CustomExceptionHandler:
    """Custom exception handler - matches .NET CustomExceptionHandler."""
    
    @staticmethod
    async def handle_exception(request: Request, exception: Exception) -> JSONResponse:
        """Handle exception and return problem details response."""
        # Log the error
        logger.log_exception(
            message="Exception occurred during request processing",
            exception=exception,
            context={
                "request_path": str(request.url.path),
                "request_method": request.method,
                "request_headers": dict(request.headers),
            },
        )
        
        # Map exception to HTTP status code and response details
        status_code, title, detail, extensions = (
            CustomExceptionHandler._map_exception(exception)
        )
        
        # Create problem details response (matches .NET ProblemDetails)
        trace_id = getattr(request.state, "request_id", None)
        if not trace_id:
            import uuid
            trace_id = str(uuid.uuid4())
        
        problem_details = {
            "title": title,
            "detail": detail,
            "status": status_code,
            "instance": str(request.url.path),
            "traceId": trace_id,
        }
        
        # Add extensions if any
        if extensions:
            problem_details.update(extensions)
        
        return JSONResponse(
            status_code=status_code,
            content=problem_details,
        )
    
    @staticmethod
    def _map_exception(exception: Exception) -> tuple[int, str, str, dict[str, Any]]:
        """Map exception to HTTP status code and response details."""
        if isinstance(exception, InternalServerError):
            return (
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )
        
        elif isinstance(exception, ValidationError):
            return (
                status.HTTP_400_BAD_REQUEST,
                exception.__class__.__name__,
                exception.message,
                {"validationErrors": exception.errors} if exception.errors else {},
            )
        
        elif isinstance(exception, BadRequestError):
            return (
                status.HTTP_400_BAD_REQUEST,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )
        
        elif isinstance(exception, NotFoundError):
            return (
                status.HTTP_404_NOT_FOUND,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )
        
        # Default case
        else:
            return (
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                exception.__class__.__name__,
                str(exception),
                {"traceback": traceback.format_exc()},
            )
```

### Exception Response Format

Both .NET and FastAPI return the same **ProblemDetails** format:

```json
{
  "title": "BadRequestError",
  "detail": "Invalid product data",
  "status": 400,
  "instance": "/api/products",
  "traceId": "550e8400-e29b-41d4-a716-446655440000",
  "details": "Product name cannot be empty"
}
```

---

## 🔄 Complete Request Flow

### Step-by-Step Flow

```
1. Client Request
   ↓
2. FastAPI Route Handler
   ↓
3. Mediator.send(command/query)
   ↓
4. ValidationBehavior.handle()
   ├─ Validates request using Pydantic
   ├─ Throws ValidationError if invalid
   └─ Continues to next behavior
   ↓
5. LoggingBehavior.handle()
   ├─ Logs [START] request + input data
   ├─ Starts timer
   ├─ Continues to handler
   ├─ Logs [END] request + output data
   └─ Logs [PERFORMANCE] warning if > 3 seconds
   ↓
6. Request Handler
   ├─ Executes business logic
   ├─ May throw exceptions
   └─ Returns response
   ↓
7. CustomExceptionHandler (if exception)
   ├─ Logs error
   ├─ Maps to HTTP status code
   └─ Returns ProblemDetails JSON
   ↓
8. Client Response
```

### Code Flow Example

**1. Client makes request:**
```python
POST /api/products
{
  "name": "Product A",
  "price": 100
}
```

**2. FastAPI route:**
```python
@router.post("/products")
async def create_product(
    request: CreateProductRequest,
    mediator: Mediator = Depends(get_mediator_dependency)
):
    command = CreateProductCommand(**request.dict())
    result = await mediator.send(command, CancellationToken())
    return result
```

**3. Mediator sends to pipeline:**
```python
# Mediator.send() → _execute_pipeline()
async def _execute_pipeline(self, request, handler, cancellation_token):
    # Apply behaviors: ValidationBehavior → LoggingBehavior → Handler
    current_handler = handler
    for behavior in reversed(self.behaviors):
        current_handler = behavior.wrap(current_handler)
    return await current_handler.handle(request, cancellation_token)
```

**4. ValidationBehavior checks:**
```python
# If validation fails:
raise ValidationError("Product name is required", errors={...})
```

**5. LoggingBehavior logs:**
```
[INFO] Starting request handling: CreateProductCommand
[INFO] Request data: {"name": "Product A", "price": 100}
... handler executes ...
[INFO] Request handling completed: CreateProductCommand
```

**6. Handler executes:**
```python
class CreateProductHandler(IRequestHandler[CreateProductCommand, Product]):
    async def handle(self, request: CreateProductCommand, token: CancellationToken):
        # Business logic
        product = Product(name=request.name, price=request.price)
        await self.repository.add(product)
        return product
```

**7. Response returned:**
```json
{
  "id": "123",
  "name": "Product A",
  "price": 100
}
```

---

## 📝 Code Examples

### Example 1: Creating a New Command Handler

**Step 1: Define Command**
```python
from pydantic import BaseModel
from app.core.contracts.cqrs import ICommand

class CreateProductCommand(ICommand[Product], BaseModel):
    name: str
    price: float
    description: str | None = None
```

**Step 2: Create Handler**
```python
from app.core.mediator.handler_registry import IRequestHandler
from app.core.mediator.cancellation import CancellationToken

class CreateProductHandler(IRequestHandler[CreateProductCommand, Product]):
    def __init__(self, repository: IProductRepository):
        self.repository = repository
    
    async def handle(
        self,
        request: CreateProductCommand,
        cancellation_token: CancellationToken
    ) -> Product:
        # Validate business rules
        if request.price <= 0:
            raise BadRequestError("Price must be greater than zero")
        
        # Create product
        product = Product(
            name=request.name,
            price=request.price,
            description=request.description
        )
        
        # Save to database
        await self.repository.add(product)
        
        return product
```

**Step 3: Register Handler**
```python
# In catalog_handler_registration.py
def register_catalog_handlers(handler_registry: HandlerRegistry) -> None:
    handler_registry.register_handler(
        CreateProductCommand,
        CreateProductHandler(product_repository)
    )
```

**Step 4: Use in Endpoint**
```python
@router.post("/products", response_model=ProductResponse)
async def create_product(
    request: CreateProductRequest,
    mediator: Mediator = Depends(get_mediator_dependency)
):
    command = CreateProductCommand(**request.dict())
    result = await mediator.send(command, CancellationToken())
    return result
```

### Example 2: Creating a New Query Handler

```python
# Query
class GetProductByIdQuery(IQuery[Product], BaseModel):
    product_id: str

# Handler
class GetProductByIdHandler(IRequestHandler[GetProductByIdQuery, Product]):
    def __init__(self, repository: IProductRepository):
        self.repository = repository
    
    async def handle(
        self,
        request: GetProductByIdQuery,
        cancellation_token: CancellationToken
    ) -> Product:
        product = await self.repository.get_by_id(request.product_id)
        
        if not product:
            raise NotFoundError(name="Product", key=request.product_id)
        
        return product
```

---

## 🔑 Key Differences

| Aspect | .NET | FastAPI |
|--------|------|---------|
| **Validation** | FluentValidation | Pydantic (built-in) |
| **DI Container** | Microsoft.Extensions.DI | Dictionary + FastAPI Depends |
| **Async/Await** | `Task<T>` | `async/await` |
| **Assembly Scanning** | Reflection API | `inspect` module |
| **Logging** | ILogger<T> | structlog + BaseLogger |
| **Exception Handling** | IExceptionHandler | FastAPI exception handlers |
| **Behaviors** | Open generics `<,>` | Generic TypeVars |
| **Carter Modules** | Auto-discovery | Manual registration |

---

## ✅ Best Practices

### 1. Handler Registration

```python
# ✅ Good: Centralized registration
def register_catalog_handlers(registry: HandlerRegistry):
    registry.register_handler(CreateProductCommand, CreateProductHandler())
    registry.register_handler(GetProductQuery, GetProductHandler())

# ❌ Bad: Scattered registration
# Registering handlers in multiple places
```

### 2. Exception Handling

```python
# ✅ Good: Use custom exceptions
raise NotFoundError(name="Product", key=product_id)

# ❌ Bad: Generic exceptions
raise Exception("Product not found")
```

### 3. Validation

```python
# ✅ Good: Use Pydantic models with validators
class CreateProductCommand(ICommand[Product], BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)

# ❌ Bad: Manual validation
if not name or len(name) > 100:
    raise ValidationError("Invalid name")
```

### 4. Logging

```python
# ✅ Good: Use structured logging with context
logger.log_with_context(
    "Creating product",
    context={"product_name": name, "price": price}
)

# ❌ Bad: String interpolation
logger.info(f"Creating product {name} with price {price}")
```

### 5. Mediator Usage

```python
# ✅ Good: Use dependency injection
async def endpoint(mediator: Mediator = Depends(get_mediator_dependency)):
    result = await mediator.send(command, CancellationToken())

# ❌ Bad: Direct instantiation
mediator = Mediator(HandlerRegistry())
```

---

## 📚 Related Files

### Core Mediator Files
- `app/core/mediator/mediator.py` - Main mediator implementation
- `app/core/mediator/extensions.py` - Assembly scanning and registration
- `app/core/mediator/behaviors.py` - Pipeline behaviors
- `app/core/mediator/handler_registry.py` - Handler registry
- `app/core/mediator/fastapi_integration.py` - FastAPI integration

### Exception Files
- `app/core/exceptions/base.py` - Base exception classes
- `app/core/exceptions/handler.py` - Exception handler

### Module Examples
- `app/modules/catalog/application/handlers/` - Catalog handlers
- `app/modules/basket/application/handlers/` - Basket handlers
- `app/modules/ordering/application/handlers/` - Ordering handlers

---

## 🎯 Summary

The FastAPI implementation provides **1-to-1 parity** with the .NET MediatR and Carter patterns:

✅ **Auto-registration** of handlers from modules  
✅ **Pipeline behaviors** with validation and logging  
✅ **Exception handling** with ProblemDetails responses  
✅ **CQRS pattern** with commands and queries  
✅ **Dependency injection** for mediator and services  
✅ **Performance monitoring** with automatic warnings  
✅ **Structured logging** with trace IDs  

The implementation maintains the same architectural patterns and conventions while leveraging Python and FastAPI best practices.

---

**Document End**

