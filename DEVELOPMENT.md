# Development Guide

This guide explains how to develop the eShop application using a hybrid approach: Docker for infrastructure services and local development for the application code.

> **First time setup?** See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for the full runbook.

## 🚀 Quick Start

### 1. Start Infrastructure Services
```bash
# Start PostgreSQL, Redis, RabbitMQ, Seq, and Keycloak
./scripts/start-infrastructure.sh
```

Uses Docker Compose when available, otherwise Podman Compose.

### 2. Provision Keycloak (if not auto-provisioned)
```bash
cp infra/keycloak/credentials.yaml.example infra/keycloak/credentials.yaml
cd backend
poetry run python scripts/provision_keycloak.py
```

See [infra/keycloak/README.md](infra/keycloak/README.md) for details.

### 3. Run Backend Locally
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run Frontend Locally
```bash
cd frontend
python -m http.server 3000
```

**Note**: Database schemas are automatically created by the custom PostgreSQL container on every startup.

## 🔧 VS Code Debugging

### Backend Debugging
1. Open VS Code in the project root
2. Go to Run and Debug (Ctrl+Shift+D)
3. Select "Debug Backend (uvicorn)" or "Debug Backend (FastAPI)"
4. Set breakpoints in your code
5. Press F5 to start debugging

### Frontend Debugging
1. Select "Debug Frontend (Chrome)" or "Debug Frontend (Edge)"
2. Set breakpoints in your JavaScript/HTML
3. Press F5 to start debugging

### Full Stack Debugging
1. Select "Debug Full Stack (Backend + Frontend)"
2. This will start both backend and frontend debugging simultaneously

## 📁 Project Structure

```
eshop-python-master/
├── backend/                 # FastAPI backend application
│   ├── app/                # Application code
│   ├── tests/              # Backend tests
│   ├── pyproject.toml      # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/               # Frontend application
│   ├── index.html          # Main page
│   ├── products.html       # Products page
│   └── Dockerfile          # Frontend container
├── scripts/                # Development scripts
│   ├── start-infrastructure.sh
│   └── stop-infrastructure.sh
├── docker-compose.yml              # Full stack (all services)
├── docker-compose.infrastructure.yml # Infrastructure only
└── .vscode/                # VS Code configuration
    ├── launch.json         # Debug configurations
    └── settings.json       # Editor settings
```

## 🐳 Docker Services

### Infrastructure Services (Docker)
- **PostgreSQL**: Database (localhost:5432)
- **Redis**: Caching (localhost:6379)
- **RabbitMQ**: Message broker (localhost:5672)
- **RabbitMQ Management**: Web UI (http://localhost:15672)
- **Keycloak**: Authentication (http://localhost:8080)

### Application Services (Local)
- **Backend**: FastAPI application (localhost:8000)
- **Frontend**: Static files (localhost:3000)

## 🔍 Debugging Tips

### Backend Debugging
- Use `print()` or `logger.debug()` for quick debugging
- Set breakpoints in VS Code for step-by-step debugging
- Check logs in the terminal where uvicorn is running
- Use FastAPI's automatic documentation at http://localhost:8000/docs

### Frontend Debugging
- Use browser developer tools (F12)
- Set breakpoints in VS Code for JavaScript debugging
- Check browser console for errors
- Use browser network tab to see API calls

### Database Debugging
- Connect to PostgreSQL: `psql -h localhost -U postgres -d eshop`
- Check RabbitMQ management UI: http://localhost:15672
- Monitor Redis: `redis-cli -h localhost`

## 🧪 Testing

### Backend Tests
```bash
cd backend
poetry run pytest
```

### VS Code Test Debugging
1. Select "Debug Backend Tests"
2. Set breakpoints in test files
3. Press F5 to run tests with debugging

## 🔧 Environment Variables

The VS Code debug configurations include all necessary environment variables:

- Database connection strings
- Redis configuration
- RabbitMQ settings
- Keycloak authentication
- CORS settings

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   # Kill the process
   kill -9 <PID>
   ```

2. **Docker Services Not Starting**
   ```bash
   # Check Docker status
   docker ps
   # Check service logs
   docker-compose -f docker-compose.infrastructure.yml logs
   ```

3. **Database Connection Issues**
   ```bash
   # Check if PostgreSQL is running
   docker ps | grep postgres
   # Test connection
   psql -h localhost -U postgres -d eshop
   ```

4. **Keycloak Not Ready**
   ```bash
   # Wait for Keycloak to fully start (can take 1-2 minutes)
   curl http://localhost:8080/realms/master
   ```

### Reset Everything
```bash
# Stop all services
./scripts/stop-infrastructure.sh
docker-compose down

# Remove all containers and volumes
docker system prune -a --volumes

# Start fresh
./scripts/start-infrastructure.sh
```

## 📚 Useful Commands

```bash
# Start infrastructure
./scripts/start-infrastructure.sh

# Stop infrastructure
./scripts/stop-infrastructure.sh

# Check service status
docker-compose -f docker-compose.infrastructure.yml ps

# View service logs
docker-compose -f docker-compose.infrastructure.yml logs -f

# Run backend with hot reload
cd backend && poetry run uvicorn app.main:app --reload

# Run tests
cd backend && poetry run pytest

# Check database
psql -h localhost -U postgres -d eshop

# Check Redis
redis-cli -h localhost ping

# Check RabbitMQ
curl -u guest:guest http://localhost:15672/api/overview
```

## 🎯 Development Workflow

1. **Start infrastructure services** (once per session)
2. **Run backend locally** with hot reload
3. **Run frontend locally** or use VS Code debugging
4. **Make changes** to code
5. **Test changes** immediately (hot reload)
6. **Debug** using VS Code breakpoints
7. **Run tests** to ensure quality
8. **Stop services** when done

This setup gives you the best of both worlds: fast local development with reliable infrastructure services.
