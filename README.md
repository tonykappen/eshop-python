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

- **Catalog Module**: Product management with CRUD operations
- **Basket Module**: Shopping cart management with Redis caching
- **Ordering Module**: Order processing and management
- **Authentication**: Keycloak integration for auth/auth
- **Logging**: Structured logging with SEQ
- **Caching**: Redis-based caching with patterns
- **Messaging**: RabbitMQ for integration events
- **Database**: PostgreSQL with SQLAlchemy and Alembic

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

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Start infrastructure services**
   ```bash
   docker-compose up -d postgres redis rabbitmq
   ```

5. **Run database migrations**
   ```bash
   poetry run alembic upgrade head
   ```

6. **Start the application**
   ```bash
   poetry run dev
   ```

## 🐳 Docker Setup

The application includes a complete Docker setup for local development:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 📁 Project Structure

```
eshop/
├── core/                    # Shared infrastructure
│   ├── cache/              # Cache patterns and implementations
│   ├── cqrs/               # CQRS abstractions
│   ├── di/                 # Dependency injection
│   ├── domain/             # DDD base classes
│   ├── logging/            # Logging configuration
│   ├── messaging/          # Integration events and outbox
│   └── repr/               # REPR pattern implementation
├── config/                 # Configuration management
├── modules/                # Business modules
│   ├── catalog/            # Product catalog
│   ├── basket/             # Shopping basket
│   └── ordering/           # Order management
├── tests/                  # Test suite
├── main.py                 # Application entry point
└── pyproject.toml          # Project configuration
```

## 🔧 Configuration

The application uses environment variables for configuration. See `env.example` for all available options.

### Key Configuration Sections:

- **Database**: PostgreSQL connection settings
- **Redis**: Cache configuration
- **RabbitMQ**: Message broker settings
- **Keycloak**: Authentication configuration
- **Logging**: SEQ and console logging settings

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=eshop

# Run specific module tests
poetry run pytest tests/modules/catalog/
```

## 📚 API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔐 Authentication

The application uses Keycloak for authentication. For development, you can:

1. Set up a local Keycloak instance
2. Create a realm and client
3. Configure the settings in `.env`

## 📊 Monitoring

- **Health Check**: http://localhost:8000/health
- **SEQ Logging**: http://localhost:5341 (if running)

## 🚀 Development

### Adding New Modules

1. Create module structure in `modules/`
2. Implement DDD entities and aggregates
3. Add CQRS commands and queries
4. Create REPR endpoints
5. Add tests
6. Register in main.py

### Code Quality

The project uses several tools for code quality:

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy .

# Security audit
poetry run bandit -r eshop/
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

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions, please refer to the project documentation or create an issue in the repository. 