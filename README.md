# eShop - Full Stack FastAPI Application

A modern, full-stack eShop application built with FastAPI (backend) and simple HTML/JavaScript (frontend), following the [FastAPI Full Stack Template](https://github.com/fastapi/full-stack-fastapi-template) structure.

## 🏗️ Architecture

This project follows a **modular monolith** architecture with **Domain-Driven Design** principles:

- **Backend**: FastAPI with Python 3.12+
- **Frontend**: Simple HTML/JavaScript interface
- **Database**: PostgreSQL with async SQLAlchemy
- **Authentication**: Keycloak with JWT tokens
- **Caching**: Redis
- **Messaging**: RabbitMQ
- **Deployment**: Docker Compose

## 📁 Project Structure

```
├── backend/                    # FastAPI backend
│   ├── app/                   # Main application code (migrated from eshop/)
│   │   ├── core/              # Core shared functionality
│   │   ├── modules/           # Business domain modules
│   │   │   ├── catalog/       # Product catalog module
│   │   │   ├── basket/        # Shopping basket module
│   │   │   └── ordering/      # Order management module
│   │   └── main.py            # FastAPI app entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend tests
│   ├── Dockerfile             # Backend container
│   └── pyproject.toml         # Python dependencies
├── frontend/                  # HTML/JavaScript frontend
│   ├── index.html             # Login page
│   ├── products.html          # Product catalog page
│   ├── Dockerfile             # Frontend container (nginx)
│   └── README.md              # Frontend documentation
├── scripts/                   # Helper scripts
├── docker-compose.yml         # Full stack deployment
└── README.md                  # This file
```

## 🚀 Quick Start

See **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** for the full runbook. Short version:

### Full stack (Docker)

```bash
docker compose up --build -d
```

Open http://localhost:3000 (frontend), http://localhost:8000/docs (API).

### Hybrid local development

```bash
./scripts/start-infrastructure.sh
cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && python3 -m http.server 3000
```

## 👥 Test Users

| Username | Password | Role    | Permissions                |
|----------|----------|---------|---------------------------|
| user     | password | user    | View products only        |
| manager  | password | manager | Read/write access         |
| adminuser| password | admin   | Full access (CRUD)        |
| testuser | password | user    | View products only        |

## 🔐 Security & RBAC

The application implements comprehensive **Role-Based Access Control**:

### Roles
- **user**: Read-only access to products
- **manager**: Read/write access to products  
- **admin**: Full access (inherits manager + user roles)

### Features
- JWT token authentication via Keycloak
- Automatic token validation on all API calls
- Role-based UI elements (admin-only buttons)
- Secure password hashing
- CORS configured for frontend-backend communication

## 🏛️ Backend Architecture

### Core Features
- **CQRS Pattern**: Separation of commands and queries
- **Mediator Pattern**: Centralized request handling
- **Repository Pattern**: Data access abstraction
- **Dependency Injection**: Clean component management
- **Event Sourcing**: Integration event support

### Modules
- **Catalog**: Product management with CRUD operations
- **Basket**: Shopping cart (add/remove items, checkout)
- **Ordering**: Order management and history

### API Endpoints
- `GET /api/v1/products/` - List products (requires: user role)
- `POST /api/v1/products/` - Create product (requires: admin/manager role)
- `GET /api/v1/products/{id}` - Get product details
- `GET /health` - Health check endpoints

## 🎨 Frontend Features

### Login Page (`index.html`)
- Keycloak authentication
- Quick login buttons for test users
- Responsive design
- Error handling

### Products Page (`products.html`)
- Product grid display with pagination
- Role-based admin controls
- Product creation modal (admin/manager only)
- Real-time token validation
- Automatic logout on session expiry

### Basket Page (`basket.html`)
- View and manage cart items
- Update quantities, remove items, checkout

### Orders Page (`orders.html`)
- View order history and order details

## 🐳 Docker Deployment

### Services
- **backend**: FastAPI application (port 8000)
- **frontend**: Nginx serving static files (port 3000)
- **postgres**: PostgreSQL database
- **redis**: Redis cache
- **rabbitmq**: Message broker (management UI on port 15672)
- **keycloak**: Authentication server (port 8080)
- **seq**: Structured log aggregation (port 5341)

### Commands
```bash
# Start all services
docker-compose up --build -d

# View logs
docker-compose logs -f [service]

# Check status
docker-compose ps

# Stop all services
docker-compose down

# Reset database
docker-compose down -v
```

## 🧪 Testing

See **[docs/TESTING.md](docs/TESTING.md)** for the full testing guide.

### Backend Tests
```bash
cd backend
poetry install
poetry run pytest app/tests/
```

### Frontend Unit Tests
```bash
cd frontend
npm ci
npm test
```

### Frontend API Contract and E2E Tests

Requires the full stack (`docker compose up -d --wait`):

```bash
cd frontend
npm ci
npx playwright install chromium
npm run test:api-contracts
npm run test:e2e
```

## 🔧 Development

### Local Backend Development
```bash
cd backend
poetry install
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/eshop" \
REDIS_URL="redis://localhost:6379" \
RABBITMQ_URL="amqp://guest:guest@localhost:5672/" \
KEYCLOAK_SERVER_URL="http://localhost:8080" \
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables
Key environment variables (see `.env`):
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/eshop
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_CLIENT_ID=eshop-api
KEYCLOAK_CLIENT_SECRET=your-client-secret
```

### Adding New Features
1. Create new modules in `backend/app/modules/`
2. Follow the existing pattern: `api/`, `application/`, `domain/`, `infrastructure/`
3. Register handlers in dependency injection
4. Add tests in `backend/tests/`
5. Update frontend if needed

## 📊 Monitoring & Health

### Health Checks
- `GET /health` - Basic health status
- `GET /health/detailed` - Detailed service status including:
  - Database connectivity
  - Redis connectivity  
  - RabbitMQ connectivity
  - Keycloak connectivity

### Logging
- Structured logging with timestamps
- Request/response logging
- Separate application and server logs
- Configurable log levels

## 🔄 Migration Notes

This project was migrated from a standalone structure to follow the [FastAPI Full Stack Template](https://github.com/fastapi/full-stack-fastapi-template):

### Key Changes
- Moved `eshop/` → `backend/app/`
- Updated all import paths from `eshop.` to `app.`
- Restructured Docker Compose for full-stack deployment
- Added simple HTML frontend replacing complex React setup
- Maintained all existing RBAC and authentication features

### Safe Migration
- All Python imports were systematically updated
- Tests were preserved and import paths corrected
- Database migrations maintained compatibility
- Configuration files adapted for new structure

## 🔐 Keycloak Provisioning

The application uses Keycloak for authentication with automated provisioning of realms, clients, roles, and users.

### Quick Setup

```bash
# 1. Create credentials file
cp infra/keycloak/credentials.yaml.example infra/keycloak/credentials.yaml
nano infra/keycloak/credentials.yaml  # Edit with your credentials

# 2. Provision Keycloak
cd backend
python scripts/provision_keycloak.py
```

### Documentation

- **[Keycloak Setup Guide](infra/keycloak/README.md)** - Complete provisioning guide
- **[Quick Reference](infra/keycloak/QUICK_REFERENCE.md)** - Common commands and examples

### Features

- ✅ No hardcoded credentials - all config in YAML file
- ✅ Realm admin creates application resources
- ✅ CLI tool for provisioning and validation
- ✅ Auto-provision on startup (optional)

For detailed instructions, see the [Keycloak documentation](infra/keycloak/README.md).

## 📚 Additional Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Infrastructure setup and running the app
- [Testing Guide](docs/TESTING.md) - Backend and frontend test layout
- [Frontend README](frontend/README.md) - Detailed frontend documentation
- [Backend API Docs](http://localhost:8000/docs) - Interactive API documentation
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup and debugging guide
- [Keycloak Setup Guide](infra/keycloak/README.md) - Keycloak provisioning guide
- [Postman Collections](tools/postman/README.md) - Manual API testing

## 🤝 Contributing

1. Follow the existing architecture patterns
2. Add tests for new features
3. Update documentation
4. Follow Python 3.12+ best practices
5. Use proper type hints and async/await

## 📄 License

This project follows the MIT license pattern of the FastAPI Full Stack Template.