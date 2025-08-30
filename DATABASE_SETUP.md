# Database Setup and Troubleshooting Guide

## Overview

The eShop application uses PostgreSQL 17 as its primary database with automatic migration and seeding at startup.

## Database Services

### PostgreSQL 17
- **Container**: `eshop-postgres`
- **Port**: `5432`
- **Database**: `eshop`
- **User**: `postgres`
- **Password**: `postgres`

### Redis 7.2
- **Container**: `eshop-redis`
- **Port**: `6379`

### RabbitMQ 3.12
- **Container**: `eshop-rabbitmq`
- **Ports**: `5672` (AMQP), `15672` (Management UI)

## Database Initialization Process

The application automatically handles database setup during startup using Python and Alembic:

1. **Wait for PostgreSQL**: The Python code waits for PostgreSQL to be ready
2. **Create Migrations**: If no migration files exist, creates initial migration using Alembic
3. **Run Migrations**: Applies all pending migrations to create tables
4. **Seed Data**: Populates initial data (catalog products, etc.)

## Expected Database Schema

After successful initialization, you should see:

### Schemas
- `public` - Default schema
- `catalog` - Catalog module tables

### Tables in `catalog` schema
- `products` - Product catalog items
- `catalog_items` - Additional catalog items
- `catalog_categories` - Product categories
- `catalog_brands` - Product brands

### Tables in `public` schema
- `alembic_version` - Migration tracking
- Various system tables

## Troubleshooting

### Issue: Cannot connect to database from pgAdmin

**Solution**: Ensure you're using the correct connection details:
- **Host**: `localhost` (or your Docker host IP)
- **Port**: `5432`
- **Database**: `eshop`
- **Username**: `postgres`
- **Password**: `postgres`

### Issue: No catalog tables found

**Possible causes**:
1. Migrations haven't run yet
2. Backend container failed to start
3. Database initialization failed

**Solutions**:

1. **Check container status**:
   ```bash
   docker-compose ps
   ```

2. **Check backend logs**:
   ```bash
   docker-compose logs backend
   ```

3. **Test database connectivity**:
   ```bash
   ./scripts/test-db-connection.sh
   ```

4. **Manually trigger database initialization**:
   ```bash
   docker-compose exec backend poetry run python -c "from app.core.database.migrations import run_migrations; run_migrations()"
   ```

5. **Reset and restart**:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Issue: Migration errors

**Common causes**:
1. Database connection issues
2. Missing dependencies
3. Permission issues

**Solutions**:

1. **Check database connection**:
   ```bash
   docker exec -it eshop-postgres psql -U postgres -d eshop -c "SELECT version();"
   ```

2. **Check migration files**:
   ```bash
   docker exec -it eshop-backend ls -la migrations/versions/
   ```

3. **Run migrations manually**:
   ```bash
   docker-compose exec backend poetry run alembic upgrade head
   ```

## Manual Database Operations

### Connect to PostgreSQL
```bash
docker exec -it eshop-postgres psql -U postgres -d eshop
```

### List all tables
```sql
\dt
```

### List tables in catalog schema
```sql
\dt catalog.*
```

### Check migration status
```sql
SELECT * FROM alembic_version;
```

### Reset database (WARNING: This will delete all data)
```bash
docker-compose down -v
docker-compose up -d postgres
# Wait for postgres to be ready, then:
docker-compose up -d backend
```

## Development Tips

1. **Use the health endpoint** to check database state:
   ```bash
   curl http://localhost:8000/health/database
   ```

2. **Monitor logs** during startup:
   ```bash
   docker-compose logs -f backend
   ```

3. **Check health endpoints**:
   ```bash
   curl http://localhost:8000/health/database
   ```

4. **Use pgAdmin** for visual database management:
   - Download pgAdmin from https://www.pgadmin.org/
   - Connect using the details above

## Production Considerations

1. **Change default passwords** in production
2. **Use environment variables** for sensitive data
3. **Set up proper backups**
4. **Configure connection pooling**
5. **Monitor database performance**

## Support

If you continue to experience issues:

1. Check the application logs: `docker-compose logs backend`
2. Verify all containers are running: `docker-compose ps`
3. Test database connectivity: `curl http://localhost:8000/health/database`
4. Check the migration status in the database
5. Review the troubleshooting steps above
