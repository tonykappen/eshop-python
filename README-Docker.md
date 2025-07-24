# Docker Setup Guide

## Prerequisites

1. **Docker Desktop** installed and running
2. **Docker Compose** (usually included with Docker Desktop)

## Quick Start

### Option 1: Automated Setup
```bash
./setup-docker.sh
```

### Option 2: Manual Setup

1. **Build the application image:**
   ```bash
   docker build -t eshop-python .
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Check service status:**
   ```bash
   docker-compose ps
   ```

## Services

The application runs with the following services:

| Service | Port | Description |
|---------|------|-------------|
| **Application** | 8000 | FastAPI application |
| **PostgreSQL** | 5432 | Database |
| **Redis** | 6379 | Cache |
| **RabbitMQ** | 5672 | Message broker |
| **RabbitMQ Management** | 15672 | RabbitMQ web UI |

## Access Points

- **Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## Useful Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f redis
docker-compose logs -f rabbitmq
```

### Stop services
```bash
docker-compose down
```

### Restart services
```bash
docker-compose restart
```

### Rebuild and restart
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Access database
```bash
docker-compose exec db psql -U eshop_user -d eshop
```

### Access Redis CLI
```bash
docker-compose exec redis redis-cli
```

## Development vs Production

### Development
- Uses volume mounts for live code reloading
- Debug mode enabled
- Hot reload with uvicorn --reload

### Production
- Build optimized image
- No volume mounts
- Production-ready settings

## Troubleshooting

### Docker daemon not running
```bash
# Start Docker Desktop
open -a Docker
```

### Port conflicts
If ports are already in use, modify `docker-compose.yml` to use different ports.

### Permission issues
```bash
# On Linux/Mac, ensure proper permissions
sudo chown -R $USER:$USER .
```

### Clean up
```bash
# Remove all containers and volumes
docker-compose down -v

# Remove all images
docker rmi eshop-python
``` 