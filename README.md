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

### Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.12+ and Poetry for local development

### 1. Start Infrastructure Services

```bash
# Start infrastructure services (PostgreSQL, Redis, RabbitMQ, Keycloak)
./scripts/start-infrastructure.sh
```

### 2. Start Application Services

```bash
# Start backend (from backend directory)
cd backend
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/eshop" \
REDIS_URL="redis://localhost:6379" \
RABBITMQ_URL="amqp://guest:guest@localhost:5672/" \
KEYCLOAK_SERVER_URL="http://localhost:8080" \
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (from frontend directory, in another terminal)
cd frontend
python3 -m http.server 3000
```

The backend will automatically:
- Set up Keycloak realm, client, roles, and users
- Run database migrations and seeding
- Provide access URLs and credentials

### 3. Database Setup

The application automatically initializes the database with:
- PostgreSQL 17 (latest stable)
- Automatic migration creation and execution using Alembic
- Initial data seeding (catalog products)
- Programmatic schema management (keycloak, catalog schemas)

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Keycloak Admin**: http://localhost:8080 (admin/admin)

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
- **Basket**: Shopping cart functionality (placeholder)
- **Ordering**: Order processing (placeholder)

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

## 🐳 Docker Deployment

### Services
- **backend**: FastAPI application (port 8000→80)
- **frontend**: Nginx serving static files (port 3000→80)
- **db**: PostgreSQL database
- **redis**: Redis cache
- **rabbitmq**: Message broker (management UI on port 15672)
- **keycloak**: Authentication server (port 8080)

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

### Backend Tests
```bash
cd backend
poetry install
poetry run pytest tests/
```

### Manual Testing
1. Start infrastructure: `./scripts/start-infrastructure.sh`
2. Start backend and frontend (see Quick Start above)
3. Open frontend: http://localhost:3000
4. Login as different users
5. Test RBAC features:
   - Regular user: can only view products
   - Manager: can view and create products
   - Admin: can view and create products

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

## 📚 Additional Documentation

- [Frontend README](frontend/README.md) - Detailed frontend documentation
- [Backend API Docs](http://localhost:8000/docs) - Interactive API documentation
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup and debugging guide

## 🤝 Contributing

1. Follow the existing architecture patterns
2. Add tests for new features
3. Update documentation
4. Follow Python 3.12+ best practices
5. Use proper type hints and async/await

## 📄 License

This project follows the MIT license pattern of the FastAPI Full Stack Template.