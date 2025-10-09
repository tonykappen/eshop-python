# Environment Variables Configuration Guide

This guide explains how to configure environment variables for the eShop application across different development scenarios.

## Overview

The application supports multiple ways to configure environment variables with the following **priority order** (highest to lowest):

1. **VS Code `launch.json`** - Direct `env` values in debug configurations
2. **`.env` file** - Root level environment file
3. **System environment variables** (`os.environ`)
4. **Default values** - Defined in `backend/app/config/settings.py`

## Quick Start

### For Local Development (Recommended)

1. **Copy the example environment file:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env`** with your local settings (already configured for localhost):
   ```bash
   # Database
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   DATABASE_NAME=eshop
   DATABASE_USER=postgres
   DATABASE_PASSWORD=postgres
   
   # Redis
   REDIS_HOST=localhost
   REDIS_PORT=6379
   
   # RabbitMQ
   RABBITMQ_HOST=localhost
   RABBITMQ_PORT=5672
   
   # Keycloak
   KEYCLOAK_SERVER_URL=http://localhost:8080
   ```

3. **Start infrastructure services:**
   ```bash
   ./scripts/start-infrastructure.sh
   ```

4. **Debug in VS Code** - The `.env` file is automatically loaded via `envFile` in `launch.json`

## Configuration Methods

### Method 1: Using .env File (Best for Local Development)

**Pros:**
- ✅ Easy to manage and version control (add `.env` to `.gitignore`)
- ✅ Works automatically with VS Code debug configurations
- ✅ Shared across all debug sessions
- ✅ Works with Pydantic BaseSettings

**Setup:**
```bash
# Create .env from template
cp env.example .env

# Edit .env with your values
nano .env
```

The application automatically loads `.env` through:
1. Pydantic's `BaseSettings` (configured in `settings.py`)
2. Custom `EnvConfig` class (in `backend/app/config/env.py`)
3. VS Code's `envFile` property in `launch.json`

### Method 2: Using launch.json Environment Variables

**Pros:**
- ✅ Configuration-specific values
- ✅ Highest priority (overrides .env)
- ✅ Good for debugging with specific settings

**Setup:**
Edit `.vscode/launch.json`:
```json
{
    "name": "Debug Backend (uvicorn)",
    "type": "python",
    "request": "launch",
    "module": "uvicorn",
    "envFile": "${workspaceFolder}/.env",  // Load .env first
    "env": {
        "PYTHONPATH": "${workspaceFolder}/backend",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_HOST": "localhost",
        // Override specific values here
    }
}
```

### Method 3: Using docker-compose Environment Variables

**Pros:**
- ✅ Best for container-based development
- ✅ Matches production-like environment
- ✅ Service discovery works automatically

**Note:** When running in Docker, the container names (e.g., `postgres`, `redis`) are used as hostnames automatically.

**For local debugging with Docker infrastructure:**
1. Start infrastructure: `./scripts/start-infrastructure.sh`
2. Use `localhost` in your `.env` file (port mappings make services available)
3. Debug backend locally in VS Code

**For full Docker development:**
```bash
docker-compose up
```

Environment variables are defined in `docker-compose.yml`:
```yaml
services:
  backend:
    environment:
      DATABASE_HOST: "postgres"  # Container name as hostname
      DATABASE_PORT: "5432"
      # ... more settings
```

### Method 4: Using docker-compose.override.yml

Create a `docker-compose.override.yml` for local overrides:

```yaml
version: '3.8'
services:
  backend:
    environment:
      DEBUG: "true"
      LOG_LEVEL: "DEBUG"
      # Your custom overrides
```

This file is automatically loaded by Docker Compose and **not** committed to git.

### Method 5: Using System Environment Variables

Set environment variables in your shell:

```bash
# Bash/Zsh
export DATABASE_HOST=localhost
export DEBUG=true

# Or load from .env
export $(cat .env | xargs)
```

## Environment Variable Loading Strategy

The application uses a sophisticated fallback strategy implemented in `backend/app/config/env.py`:

```python
from app.config.env import get_env, get_env_bool, get_env_int

# Get with default
db_host = get_env("DATABASE_HOST", "localhost")

# Get boolean
debug = get_env_bool("DEBUG", False)

# Get integer
port = get_env_int("PORT", 8000)
```

**Loading order:**
1. Check `launch.json` env vars (VS Code debugging)
2. Check `.env` file
3. Check `os.environ` (system environment)
4. Return default value or raise `ValueError`

## Available Environment Variables

See `env.example` for the complete list. Key variables:

### Application
- `APP_NAME` - Application name
- `APP_VERSION` - Application version
- `DEBUG` - Enable debug mode (true/false)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

### Database
- `DATABASE_HOST` - PostgreSQL host
- `DATABASE_PORT` - PostgreSQL port (default: 5432)
- `DATABASE_NAME` - Database name
- `DATABASE_USER` - Database user
- `DATABASE_PASSWORD` - Database password

### Redis
- `REDIS_HOST` - Redis host
- `REDIS_PORT` - Redis port (default: 6379)
- `REDIS_DB` - Redis database number

### RabbitMQ
- `RABBITMQ_HOST` - RabbitMQ host
- `RABBITMQ_PORT` - RabbitMQ port (default: 5672)
- `RABBITMQ_USER` - RabbitMQ user
- `RABBITMQ_PASSWORD` - RabbitMQ password

### Keycloak
- `KEYCLOAK_SERVER_URL` - Keycloak server URL
- `KEYCLOAK_REALM` - Keycloak realm name
- `KEYCLOAK_CLIENT_ID` - Client ID
- `KEYCLOAK_CLIENT_SECRET` - Client secret

### Logging
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_ENABLE_SEQ` - Enable Seq logging (true/false)
- `SEQ_URL` - Seq server URL
- `SEQ_API_KEY` - Seq API key
- `LOG_ENABLE_FILE` - Enable file logging (true/false)
- `LOG_DIRECTORY` - Log directory path

## Common Scenarios

### Scenario 1: Debug Backend with Local Infrastructure

```bash
# 1. Start infrastructure
./scripts/start-infrastructure.sh

# 2. Ensure .env has localhost values
DATABASE_HOST=localhost
REDIS_HOST=localhost
RABBITMQ_HOST=localhost
KEYCLOAK_SERVER_URL=http://localhost:8080

# 3. Press F5 in VS Code (or use "Debug Backend (uvicorn)")
```

### Scenario 2: Run Full Stack in Docker

```bash
# Uses docker-compose.yml environment values
docker-compose up

# Backend uses container names (postgres, redis, etc.)
```

### Scenario 3: Debug Tests

```bash
# Uses .env + TESTING=true from launch.json
# Select "Debug Backend Tests" in VS Code
```

### Scenario 4: Custom Configuration per Debug Session

Edit `.vscode/launch.json` to add a new configuration:

```json
{
    "name": "Debug Backend (Production Mode)",
    "type": "python",
    "request": "launch",
    "module": "uvicorn",
    "envFile": "${workspaceFolder}/.env",
    "env": {
        "PYTHONPATH": "${workspaceFolder}/backend",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
        "LOG_ENABLE_SEQ": "true"
    }
}
```

## Best Practices

1. **Never commit `.env`** - Add to `.gitignore`
2. **Always update `env.example`** when adding new variables
3. **Use `.env` for local development** - Most convenient
4. **Use `launch.json` env for debug-specific overrides** - Highest priority
5. **Document all environment variables** - Update this file and `env.example`
6. **Use strong secrets in production** - Don't use default values
7. **Validate environment variables** - The app will raise errors if critical vars are missing

## Troubleshooting

### Problem: Environment variables not loading

**Solution:**
1. Check file path: `.env` should be in the project root
2. Verify syntax: `KEY=value` (no spaces around `=`)
3. Check VS Code terminal: Ensure `envFile` is correctly specified
4. Restart VS Code debug session

### Problem: Wrong values being used

**Solution:**
Check the priority order:
1. `launch.json` env values (highest)
2. `.env` file
3. System environment variables
4. Default values (lowest)

Use this to debug:
```python
from app.config.env import get_all_env
print(get_all_env())  # See all loaded environment variables
```

### Problem: Docker vs Local Development confusion

**Solution:**
- **Local debugging**: Use `localhost` for all services in `.env`
- **Docker debugging**: Use container names (`postgres`, `redis`, etc.)

## See Also

- `env.example` - Template with all available variables
- `backend/app/config/settings.py` - Settings class with defaults
- `backend/app/config/env.py` - Environment loading implementation
- `docker-compose.yml` - Docker environment configuration
- `.vscode/launch.json` - VS Code debug configurations

