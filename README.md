# eShop Modular Monolith (Python/FastAPI)

A modular monolith e-commerce application migrated from .NET to Python using FastAPI, implementing Domain-Driven Design (DDD), CQRS, and other enterprise patterns.

## 🏗️ Architecture

This application follows a **Modular Monolith** architecture with the following patterns:

- **Domain-Driven Design (DDD)**: Aggregates, Entities, Value Objects, Domain Events
- **CQRS**: Command Query Responsibility Segregation
- **REPR Pattern**: Request-Endpoint-Response pattern for all API endpoints
- **Outbox Pattern**: Reliable event publishing
- **Cache Aside Pattern**: Redis caching with invalidation
- **Dependency Injection**: Assembly scanning and scoped services
- **Integration Events**: Cross-module communication via RabbitMQ

## 🚀 Features

### ✅ **Milestone 1: Core Infrastructure (COMPLETED)**
- **DDD Base Classes**: Entity, Aggregate, ValueObject, DomainEvent with audit fields
- **CQRS Abstractions**: ICommand, IQuery, ICommandHandler, IQueryHandler
- **Outbox Pattern**: Reliable event publishing with OutboxMessage
- **Authentication**: Keycloak integration for JWT token validation
- **Health Checks**: Comprehensive health checks for all services (DB, Redis, RabbitMQ, Keycloak)
- **Logging**: Structured logging with structlog and SEQ support
- **Caching**: Redis-based caching with CacheAside and CacheInvalidation patterns
- **Messaging**: RabbitMQ integration with FastStream for integration events
- **Database**: PostgreSQL with SQLAlchemy and Alembic support
- **Object Mapping**: High-performance serialization with msgspec
- **Retry Mechanisms**: Tenacity for handling transient failures
- **Pagination**: FastAPI-pagination for standardized pagination
- **Assembly Scanning**: Automatic service discovery and registration
- **REPR Pattern**: Request-Endpoint-Response pattern for all API endpoints
- **Dependency Injection**: Container setup with configuration

### 🔄 **Upcoming Milestones**
- **Milestone 2**: Catalog Module Migration (Product CRUD operations)
- **Milestone 3**: Basket Module Migration (Shopping cart management)
- **Milestone 4**: Ordering Module Migration (Order processing)
- **Milestone 5**: Messaging, Outbox, and Integration
- **Milestone 6**: Documentation, Handover, and Final Review

## 📋 Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker & Docker Compose
- PostgreSQL
- Redis
- RabbitMQ
- Keycloak (optional for development)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd eshop
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up pre-commit hooks**
   ```bash
   poetry run pre-commit install
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Start infrastructure services**
   ```bash
   docker-compose up -d postgres redis rabbitmq
   ```

6. **Run database migrations**
   ```bash
   poetry run alembic upgrade head
   ```

7. **Start the application**
   ```bash
   poetry run dev
   ```

## 🐳 Docker Setup

### Using Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down
```

### Using Podman
```bash
# Run the setup script
./setup-podman.sh
```

## 🧪 Testing

### Current Status
**Milestone 1** focuses on core infrastructure. Module-specific tests will be added in subsequent milestones.

### Testing Tools Available
```bash
# Run all tests (currently no tests for Milestone 1)
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=eshop --cov-report=html

# Run specific test file
poetry run pytest tests/test_catalog.py

# Run tests with httpx for async testing
poetry run pytest tests/ -v
```

### Manual Testing
You can test the current implementation:

```bash
# Start the application
poetry run uvicorn eshop.main:app --host 0.0.0.0 --port 8000 --reload

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
curl http://localhost:8000/docs
```

### Testing Tools
- **pytest**: Test framework
- **httpx**: Async HTTP client for testing
- **respx**: HTTP request mocking
- **faker**: Test data generation

## 🔧 Development Tools

### Code Quality
```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy .

# Security audit
poetry run bandit -r eshop/

# Sort imports
poetry run isort .
```

### Pre-commit Hooks
The project uses pre-commit hooks for automatic code quality checks:
- **Black**: Code formatting
- **Ruff**: Linting and formatting
- **MyPy**: Type checking
- **Bandit**: Security scanning
- **isort**: Import sorting

## 📦 Key Technologies

### Core Framework
- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation and settings

### Database & ORM
- **SQLAlchemy**: ORM and database toolkit
- **Alembic**: Database migrations
- **PostgreSQL**: Primary database

### Messaging & Caching
- **FastStream**: Modern async messaging framework
- **Redis**: Caching and session storage
- **RabbitMQ**: Message broker

### Object Mapping & Serialization
- **msgspec**: High-performance serialization and validation
- **Pydantic**: Data validation and serialization

### Retry & Resilience
- **Tenacity**: Retry mechanisms for transient failures

### Pagination
- **fastapi-pagination**: Standardized pagination support

### Dependency Injection
- **dependency-injector**: DI container
- **Assembly Scanning**: Automatic service discovery

### Logging
- **structlog**: Structured logging

### Testing
- **pytest**: Test framework
- **httpx**: Async HTTP client
- **respx**: HTTP mocking
- **faker**: Test data generation

## 🏛️ Project Structure

```
eshop/
├── core/                    # Shared core functionality
│   ├── cqrs/               # CQRS base classes
│   ├── domain/             # DDD base classes
│   ├── di/                 # Dependency injection
│   ├── mapping/            # Object mapping with msgspec
│   ├── messaging/          # FastStream messaging
│   ├── pagination/         # Pagination models
│   ├── retry/              # Tenacity retry mechanisms
│   └── logging/            # Structured logging
├── modules/                # Business modules
│   ├── catalog/            # Product catalog
│   ├── basket/             # Shopping basket
│   └── ordering/           # Order management
├── config/                 # Configuration
├── tests/                  # Test suite
└── main.py                 # Application entry point
```

## 🔐 Authentication

The application uses Keycloak for authentication. For development, you can:

1. Set up a local Keycloak instance
2. Create a realm and client
3. Configure the settings in `.env`

## 📊 Monitoring & Health Checks

### Available Endpoints
- **Basic Health**: http://localhost:8000/health
- **API Health**: http://localhost:8000/api/v1/health
- **Detailed Health**: http://localhost:8000/health/detailed
- **Database Health**: http://localhost:8000/health/database
- **Redis Health**: http://localhost:8000/health/redis
- **RabbitMQ Health**: http://localhost:8000/health/rabbitmq
- **Keycloak Health**: http://localhost:8000/health/keycloak
- **OpenAPI Docs**: http://localhost:8000/docs
- **Authentication Test**: http://localhost:8000/api/v1/auth/me (requires Bearer token)

### Health Check Response Example
```json
{
  "status": "unhealthy",
  "timestamp": "2025-08-01T18:00:37.251138",
  "version": "0.1.0",
  "services": {
    "database": {
      "status": "unhealthy",
      "service": "database",
      "error": "Connection refused",
      "host": "localhost",
      "port": 5432
    },
    "redis": {
      "status": "unhealthy", 
      "service": "redis",
      "error": "Connection refused",
      "host": "localhost",
      "port": 6379
    }
  }
}
```

## 🚀 Development

### Adding New Modules

1. Create module structure in `modules/`
2. Implement DDD entities and aggregates
3. Add CQRS commands and queries
4. Create REPR endpoints
5. Add tests
6. Register in main.py

### Service Registration

Use decorators for automatic service registration:

```python
from eshop.core.di.assembly_scanner import singleton_service

@singleton_service("product_repository")
class ProductRepository:
    pass
```

### Object Mapping

Use msgspec for high-performance serialization:

```python
from eshop.core.mapping.mapper import map_to_dto, to_json

# Map entity to DTO
product_dto = map_to_dto(product_entity, ProductDto)

# Serialize to JSON
json_data = to_json(product_dto)
```

### Retry Mechanisms

Use tenacity for handling transient failures:

```python
from eshop.core.retry.retry import retry_database_operation

@retry_database_operation
async def save_product(product: Product):
    # Database operation with automatic retry
    pass
```

## 📦 Deployment

The application is containerized and ready for deployment:

```bash
# Build image
docker build -t eshop .

# Run container
docker run -p 8000:8000 eshop
```

## 🤝 Contributing

1. Follow the established patterns (DDD, CQRS, REPR)
2. Write tests for new features
3. Update documentation
4. Ensure code quality checks pass
5. Use pre-commit hooks

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions, please refer to the project documentation or create an issue in the repository. 