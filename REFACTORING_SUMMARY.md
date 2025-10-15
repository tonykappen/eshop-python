# Infrastructure Refactoring Summary

**Date:** October 10, 2025  
**Type:** Major Architectural Change

## Overview

This refactoring reorganizes the database migration system and infrastructure provisioning to follow a modular, per-module approach. The changes improve code organization, modularity, and align with Domain-Driven Design principles.

## Key Changes

### 1. Infrastructure Directory Structure

**Created:** `infra/` directory for external service provisioning

```
infra/
└── keycloak/
    ├── __init__.py
    └── keycloak_setup.py
```

**Moved:** Keycloak setup from `backend/app/core/auth/keycloak_setup.py` to `infra/keycloak/keycloak_setup.py`

**Reason:** Separate infrastructure provisioning from application core logic. Keycloak is external infrastructure, not core business logic.

### 2. Per-Module Database Migrations

**Created:** Individual Alembic configurations for each module:

```
backend/app/modules/
├── catalog/
│   ├── alembic/
│   │   ├── versions/001_initial_migration.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   └── infrastructure/orm_models.py
├── basket/
│   ├── alembic/
│   │   ├── versions/001_initial_migration.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   └── infrastructure/orm_models.py
└── ordering/
    ├── alembic/
    │   ├── versions/001_initial_migration.py
    │   ├── env.py
    │   └── script.py.mako
    ├── alembic.ini
    └── infrastructure/orm_models.py
```

**Deprecated:** `backend/alembic/` (monolithic migration configuration)

**Reason:** 
- Each module manages its own database schema
- Better modularity and independence
- Aligns with modular monolith architecture
- Each module has its own PostgreSQL schema

### 3. Schema Management

**Added:** Automatic schema creation in migrations

**Modified:** `app/core/database/migrations.py` to:
- Create schemas automatically (catalog, basket, ordering, keycloak)
- Run per-module migrations
- Handle module-specific configurations

**Modified:** `docker/postgres/ensure-schemas.sh` to remove manual schema creation

**Reason:** Schema creation is now part of the migration process, not infrastructure setup.

### 4. ORM Models

**Created:** ORM models for basket and ordering modules:
- `backend/app/modules/basket/infrastructure/orm_models.py`
- `backend/app/modules/ordering/infrastructure/orm_models.py`

**Reason:** Each module needs its own ORM models with proper schema definitions.

## Files Modified

### Created
- `infra/__init__.py`
- `infra/keycloak/__init__.py`
- `infra/keycloak/keycloak_setup.py`
- `backend/app/modules/catalog/alembic.ini` (active)
- `backend/app/modules/catalog/alembic/env.py` (active)
- `backend/app/modules/catalog/alembic/script.py.mako` (active)
- `backend/app/modules/catalog/alembic/versions/001_initial_migration.py` (active)
- `backend/app/modules/basket/alembic.ini` (placeholder)
- `backend/app/modules/basket/alembic/env.py` (placeholder)
- `backend/app/modules/basket/alembic/script.py.mako` (placeholder)
- `backend/app/modules/basket/alembic/versions/001_initial_migration.py` (placeholder)
- `backend/app/modules/basket/infrastructure/orm_models.py` (placeholder)
- `backend/app/modules/ordering/alembic.ini` (placeholder)
- `backend/app/modules/ordering/alembic/env.py` (placeholder)
- `backend/app/modules/ordering/alembic/script.py.mako` (placeholder)
- `backend/app/modules/ordering/alembic/versions/001_initial_migration.py` (placeholder)
- `backend/app/modules/ordering/infrastructure/orm_models.py` (placeholder)
- `MIGRATIONS_PER_MODULE.md` (documentation)
- `REFACTORING_SUMMARY.md` (this file)
- `backend/alembic/DEPRECATED.md` (deprecation notice)

**Note:** Currently only the **catalog module** is fully implemented with real migrations. Basket and ordering modules have placeholder files to enable the per-module system but don't create any tables yet.

### Modified
- `backend/app/core/lifecycle/handlers.py` - Updated import to use new keycloak location
- `backend/app/core/database/migrations.py` - Complete rewrite for per-module migrations
- `docker/postgres/ensure-schemas.sh` - Removed schema creation

### Deleted
- `backend/app/core/auth/keycloak_setup.py` - Moved to infra/keycloak/

## Database Schema Structure

### Before
```
public:
  - alembic_version
  - mixed tables or catalog schema only
```

### After
```
catalog:
  - alembic_version
  - products
  - catalog_items
  - catalog_categories
  - catalog_brands

basket:
  - alembic_version
  - baskets
  - basket_items

ordering:
  - alembic_version
  - orders
  - order_items

keycloak:
  - (managed by Keycloak service)
```

## Migration Process

### Automatic (On Application Startup) ✅ PRIMARY METHOD
Migrations run **automatically** when the app starts:
1. Wait for database to be ready
2. Ensure schemas exist (catalog, keycloak)
3. Run migrations for catalog module
4. Continue with application startup

**You don't need to run migrations manually** - just start the app!

### Manual (Only for Development/Testing)
If you need to create new migrations after modifying ORM models:

```bash
cd backend

# Create new migration for catalog module
poetry run alembic -c app/modules/catalog/alembic.ini revision --autogenerate -m "Add new feature"

# Check migration status (optional)
poetry run alembic -c app/modules/catalog/alembic.ini current
```

## Benefits

### 1. Modularity
- Each module is self-contained with its own migrations
- Can develop and test modules independently
- Clear boundaries between modules

### 2. Schema Isolation
- PostgreSQL schemas prevent naming conflicts
- Better security (can grant permissions per schema)
- Clearer data organization

### 3. Independent Evolution
- Modules can evolve their schemas independently
- No cross-module migration dependencies
- Easier to add/remove modules

### 4. Better Organization
- Infrastructure code separated from application core
- Clear separation of concerns
- Follows Domain-Driven Design principles

### 5. Simplified Docker Setup
- No manual schema creation needed
- Everything handled by migrations
- Consistent across environments

## Backward Compatibility

### Breaking Changes
- Old monolithic migrations (`backend/alembic/`) are deprecated
- Need to migrate existing databases (see migration guide)

### Migration Path
For existing databases:
1. Back up your database
2. Follow migration guide in `MIGRATIONS_PER_MODULE.md`
3. Stamp new per-module migrations
4. Remove old version tracking

For new deployments:
- No action needed, new system will be used automatically

## Current Implementation Status

### ✅ Fully Implemented
- **Catalog Module**: Complete with real migrations and ORM models
  - Products table
  - Catalog items, categories, brands tables
  - Full Alembic configuration

### 📦 Placeholder (Future Implementation)
- **Basket Module**: Infrastructure ready, models pending
- **Ordering Module**: Infrastructure ready, models pending

### 🔄 Migration System
- **Automatic execution**: Runs on app startup (no manual intervention needed)
- **Per-module**: Each module manages its own schema
- **Schema creation**: Automatic (catalog, keycloak)

## Testing Checklist

- [x] Catalog module has full Alembic configuration and migrations
- [x] Basket and ordering have placeholder configurations
- [x] Schema creation is automatic
- [x] Keycloak setup works from new location
- [x] No linter errors in new code
- [x] Documentation created

## Next Steps

### For Development Team
1. Read `MIGRATIONS_PER_MODULE.md` for detailed usage
2. When creating new tables, use the module's alembic configuration
3. Always specify the schema in `__table_args__`

### For Deployment
1. Test migration in staging environment first
2. Back up production database before deploying
3. Follow migration guide for existing databases
4. Verify all schemas are created correctly

## Related Documentation

- `MIGRATIONS_PER_MODULE.md` - Complete migration guide
- `backend/alembic/DEPRECATED.md` - Old system deprecation notice
- `ENVIRONMENT_VARIABLES.md` - Environment configuration
- `DEVELOPMENT.md` - Development setup

## Questions or Issues?

If you encounter any issues with the new migration system:
1. Check the troubleshooting section in `MIGRATIONS_PER_MODULE.md`
2. Verify your database connection settings
3. Ensure all schemas are created correctly
4. Check module-specific alembic_version tables

## Credits

This refactoring improves the modular monolith architecture by ensuring database schemas align with module boundaries, following best practices from Domain-Driven Design and the .NET eShop reference application.

