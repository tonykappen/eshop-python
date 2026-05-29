# Getting Started

This guide is the canonical runbook for starting infrastructure and running the eShop application.

## Prerequisites

- **Docker** and **Docker Compose** (recommended for full stack)
- **Poetry** (Python 3.12+) for local backend development
- **Node.js 20+** (optional, for frontend unit tests only)

## Service Map

| Service | Container name | Port | URL |
|---------|----------------|------|-----|
| Frontend | `eshop-frontend` | 3000 | http://localhost:3000 |
| Backend API | `eshop-backend` | 8000 | http://localhost:8000/docs |
| PostgreSQL | `eshop-postgres` | 5432 | `postgresql://postgres:postgres@localhost:5432/eshop` |
| Redis | `eshop-redis` | 6379 | `redis://localhost:6379` |
| RabbitMQ | `eshop-rabbitmq` | 5672, 15672 | http://localhost:15672 (guest/guest) |
| Keycloak | `eshop-keycloak` | 8080 | http://localhost:8080 (admin/admin) |
| Seq (logs) | `eshop-seq` | 5341 | http://localhost:5341 |

## Option A: Full Stack with Docker (Recommended)

Start all infrastructure and application services:

```bash
# From the repository root
docker compose up --build -d
```

Wait for health checks to pass, then verify:

```bash
docker compose ps
docker compose logs -f backend   # migrations, Keycloak provisioning, startup
```

### Access the application

| Resource | URL |
|----------|-----|
| Frontend (login) | http://localhost:3000 |
| Products | http://localhost:3000/products.html |
| Basket | http://localhost:3000/basket.html |
| Orders | http://localhost:3000/orders.html |
| API docs | http://localhost:8000/docs |
| Keycloak admin | http://localhost:8080 |

### Stop and reset

```bash
docker compose down          # stop services
docker compose down -v       # stop and remove volumes (fresh database)
```

## Option B: Hybrid Local Development

Run infrastructure in Docker and the application locally for faster iteration.

### 1. Start infrastructure only

```bash
./scripts/start-infrastructure.sh
```

This script uses **Docker Compose** when available, otherwise falls back to **Podman**.

### 2. Configure environment

```bash
cp env.example .env
```

See [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) for all options.

### 3. Run the backend

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup the backend will:

- Run database migrations
- Seed catalog data
- Provision Keycloak realm, client, roles, and users (when configured)

### 4. Run the frontend

```bash
cd frontend
python3 -m http.server 3000
```

Open http://localhost:3000.

## Keycloak Setup

Keycloak is provisioned automatically on backend startup when credentials are configured.

For manual provisioning:

```bash
cp infra/keycloak/credentials.yaml.example infra/keycloak/credentials.yaml
# Edit credentials.yaml with your values

cd backend
poetry run python scripts/provision_keycloak.py
```

See [infra/keycloak/README.md](../infra/keycloak/README.md) for details.

## Test Users

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| user | password | user | View products, manage own basket/orders |
| manager | password | manager | Read/write products |
| adminuser | password | admin | Full access (CRUD) |
| testuser | password | user | View products only |

## Running Tests

### Backend

```bash
cd backend
poetry install
poetry run pytest app/tests/
```

### Frontend unit tests

```bash
cd frontend
npm ci
npm test
```

See [TESTING.md](TESTING.md) for test layout and markers.

## Troubleshooting

### Stale session / 401 after Keycloak reset

Keycloak signing keys change when volumes are wiped. Log out and log in again. The frontend clears invalid tokens automatically.

### Backend won't start — database not ready

```bash
docker compose ps postgres
docker compose logs postgres
```

Ensure PostgreSQL is healthy before the backend starts. In hybrid mode, wait ~10 seconds after `./scripts/start-infrastructure.sh`.

### Port already in use

```bash
lsof -i :8000    # backend
lsof -i :3000    # frontend
lsof -i :5432    # postgres
```

### View logs

```bash
docker compose logs -f backend
docker compose logs -f keycloak
```

Seq dashboard at http://localhost:5341 aggregates structured application logs when `LOG_ENABLE_SEQ=true`.

## Related Documentation

- [ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) — configuration reference
- [DEVELOPMENT.md](../DEVELOPMENT.md) — VS Code debugging, hybrid workflow
- [frontend/README.md](../frontend/README.md) — frontend pages and API integration
- [infra/keycloak/README.md](../infra/keycloak/README.md) — Keycloak provisioning
- [tools/postman/README.md](../tools/postman/README.md) — manual API testing collections
