# eShop Docker Compose Setup

This document provides instructions for setting up and running the eShop application using Docker Compose.

## 🚀 Quick Start

### Prerequisites

1. **Docker Desktop** installed and running
2. **Docker Compose** (usually included with Docker Desktop)
3. **Git** for cloning the repository

### Setup Instructions

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd eshop-python-master
   ```

2. **Run the complete setup**:
   ```bash
   ./setup-docker-compose.sh
   ```

   This script will:
   - Build and start all services
   - Wait for services to be ready
   - Set up Keycloak with proper configuration
   - Create test users with roles
   - Test the application

3. **Alternative: Manual setup**:
   ```bash
   # Start services
   ./docker-compose-start.sh
   
   # Wait for services to be ready, then run:
   ./setup-keycloak.sh
   ./create-users.sh
   ```

## 📋 Services

The docker-compose setup includes the following services:

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 3000 | React/HTML frontend served by Nginx |
| **Backend** | 8000 | FastAPI application |
| **Keycloak** | 8080 | Authentication and authorization server |
| **PostgreSQL** | 5432 | Database |
| **Redis** | 6379 | Caching |
| **RabbitMQ** | 5672, 15672 | Message broker and management |

## 🔐 Authentication

### Test Users

The setup creates the following test users:

| Username | Password | Role | Access Level |
|----------|----------|------|--------------|
| `user` | `password` | User | Read-only access |
| `manager` | `password` | Manager | Read/write access |
| `adminuser` | `password` | Admin | Full access |
| `testuser` | `password` | User | Read-only access |

### Login Commands

```bash
# Get access token
curl -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret"

# Use token to access API
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/products/
```

## 🌐 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/detailed
- **Keycloak Admin**: http://localhost:8080/admin/ (admin/admin)
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 🔧 Management Commands

### Start/Stop Services

```bash
# Start services
./docker-compose-start.sh
# or
docker-compose up -d

# Stop services
./docker-compose-stop.sh
# or
docker-compose down

# Restart services
docker-compose restart

# Rebuild and start
docker-compose up --build -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f keycloak
```

### Service Status

```bash
# Check service status
docker-compose ps

# Check service health
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

## 🐛 Troubleshooting

### Common Issues

1. **Docker daemon not running**:
   ```bash
   # Start Docker Desktop
   # On macOS: Open Docker Desktop application
   # On Linux: sudo systemctl start docker
   ```

2. **Port conflicts**:
   ```bash
   # Check what's using the ports
   lsof -i :8000
   lsof -i :3000
   lsof -i :8080
   
   # Stop conflicting services or change ports in docker-compose.yml
   ```

3. **Services not starting**:
   ```bash
   # Check logs
   docker-compose logs backend
   docker-compose logs keycloak
   
   # Restart services
   docker-compose restart
   ```

4. **Keycloak setup issues**:
   ```bash
   # Wait for Keycloak to be ready
   curl -s http://localhost:8080/realms/eshop
   
   # Re-run setup
   ./setup-keycloak.sh
   ./create-users.sh
   ```

### Reset Everything

```bash
# Stop and remove everything
docker-compose down -v
docker system prune -f

# Rebuild from scratch
./setup-docker-compose.sh
```

## 📁 File Structure

```
eshop-python-master/
├── docker-compose.yml              # Main compose file
├── setup-docker-compose.sh         # Complete setup script
├── docker-compose-start.sh         # Start services
├── docker-compose-stop.sh          # Stop services
├── setup-keycloak.sh              # Keycloak configuration
├── create-users.sh                # User creation script
├── backend/
│   ├── Dockerfile                 # Backend container
│   ├── app/                       # Application code
│   └── pyproject.toml            # Python dependencies
└── frontend/
    ├── Dockerfile                 # Frontend container
    ├── nginx.conf                 # Nginx configuration
    └── *.html                     # Static files
```

## 🔄 Development Workflow

### Making Changes

1. **Backend changes**:
   ```bash
   # Rebuild backend
   docker-compose build backend
   docker-compose up -d backend
   ```

2. **Dependency updates**:
   ```bash
   # Check for outdated dependencies
   ./update-dependencies.sh check
   
   # Regenerate lock file (recommended)
   ./update-dependencies.sh lock
   
   # Force update all dependencies (use with caution)
   ./update-dependencies.sh force
   ```

2. **Frontend changes**:
   ```bash
   # Rebuild frontend
   docker-compose build frontend
   docker-compose up -d frontend
   ```

3. **Configuration changes**:
   ```bash
   # Restart affected services
   docker-compose restart backend
   ```

### Adding New Services

1. Add service definition to `docker-compose.yml`
2. Create Dockerfile if needed
3. Update setup scripts if required
4. Test with `docker-compose up -d`

## 🧪 Testing

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed

# Frontend
curl http://localhost:3000
```

### API Testing

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret" \
  | jq -r '.access_token')

# Test API
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/products/
```

## 📝 Notes

- All services use the `eshop-network` network for communication
- Persistent data is stored in Docker volumes
- Health checks ensure services are ready before dependent services start
- The setup includes proper RBAC (Role-Based Access Control) configuration
- Frontend is served by Nginx for better performance
- Backend includes comprehensive logging and monitoring

## 🔄 Dependency Management

The backend Dockerfile includes robust dependency management:

### Build Arguments
- `CACHEBUST`: Forces cache invalidation (default: timestamp)
- `UPDATE_DEPS`: Controls dependency update behavior (default: false)

### Dependency Resolution
- **Lock file validation**: Ensures `poetry.lock` matches `pyproject.toml`
- **Cache busting**: Prevents stale dependency cache issues
- **Flexible updates**: Can update dependencies when needed

### Update Strategies
1. **Conservative** (`UPDATE_DEPS=false`): Uses existing lock file
2. **Aggressive** (`UPDATE_DEPS=true`): Updates to latest compatible versions
3. **Lock regeneration**: Regenerates lock file from `pyproject.toml`

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs -f`
3. Verify Docker Desktop is running
4. Ensure ports are not in use by other applications
5. Try the reset procedure if all else fails
