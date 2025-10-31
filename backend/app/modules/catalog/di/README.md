# Catalog Module DI Structure

## Overview

Clean, focused dependency injection structure for the catalog module with FastAPI integration.

## Structure

```
catalog/di/
├── __init__.py          # Module exports
├── container.py         # CatalogContainer implementation
├── providers.py         # Service providers and factories
├── wiring.py           # FastAPI integration and wiring
└── README.md           # This file
```

## Core Components

### 1. Container (`container.py`)
- **CatalogContainer**: Main DI container with singleton, factory, and scoped services
- **Service Registration**: Register services with different lifecycles
- **Service Resolution**: Get services from container with proper error handling
- **Scope Management**: Request-scoped service management

### 2. Providers (`providers.py`)
- **Database Services**: Engine, session maker, session management
- **Repository Services**: Product, category, inventory repositories
- **Application Services**: Unit of Work, request context, mediator
- **Messaging Services**: Message bus, dispatcher, outbox pattern

### 3. Wiring (`wiring.py`)
- **FastAPI Integration**: Dependency overrides for seamless integration
- **Service Registration**: Automatic service registration
- **Domain Events**: Domain event subscription and handling

## Usage

### Basic Usage
```python
from app.modules.catalog.di import get_catalog_container, wire_catalog_dependencies

# Get container and wire dependencies
container = get_catalog_container()
wire_catalog_dependencies(container)

# Get services
engine = container.get(type(get_catalog_engine()))
```

### FastAPI Integration
```python
from app.modules.catalog.catalog_module import register_catalog_module_with_fastapi

# Register with FastAPI app
catalog_router = register_catalog_module_with_fastapi(app, container, mediator)
app.include_router(catalog_router)
```

## Testing

Integration tests are located in `/backend/app/tests/test_catalog_di_integration.py`:

- **Container Tests**: Basic container functionality
- **Service Registration Tests**: Service registration and retrieval
- **Integration Tests**: Full DI integration testing

## Key Features

- ✅ **Clean Architecture**: Proper separation of concerns
- ✅ **FastAPI Integration**: Seamless dependency injection
- ✅ **Service Lifecycle**: Singleton, factory, and scoped services
- ✅ **Domain Events**: Event-driven architecture support
- ✅ **Testability**: Easy mocking and testing
- ✅ **Maintainability**: Centralized dependency management
