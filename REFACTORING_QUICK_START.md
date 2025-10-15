# Infrastructure Refactoring - Quick Start

## What Changed?

### 1. ✅ Keycloak Setup Moved to `infra/keycloak`
- **Before**: `backend/app/core/auth/keycloak_setup.py`
- **After**: `infra/keycloak/keycloak_setup.py`
- **Why**: Infrastructure provisioning separated from core business logic

### 2. ✅ Per-Module Database Migrations (Catalog Module Active)
- **Catalog Module**: Fully implemented with Alembic migrations
- **Basket/Ordering Modules**: Placeholder files for future implementation
- **Automatic**: Migrations run on app startup - **no manual intervention needed!**

## Current State

### Active: Catalog Module 
```
backend/app/modules/catalog/
├── alembic/
│   ├── versions/001_initial_migration.py  ← Creates catalog tables
│   ├── env.py                             ← Auto-creates catalog schema
│   └── script.py.mako
├── alembic.ini
└── infrastructure/
    └── orm_models.py                      ← Products, categories, brands, items
```

**Database Schema Created:**
- `catalog.products`
- `catalog.catalog_items`
- `catalog.catalog_categories`
- `catalog.catalog_brands`

### Placeholders: Basket & Ordering Modules
- Infrastructure ready (alembic folders, env.py, ini files)
- ORM models are empty placeholders with TODO comments
- Will be implemented when those modules are developed

## How Migrations Work

### ✨ Automatic Execution (No Action Needed!)

When you start the application:

```python
# This happens automatically in app/core/database/migrations.py

1. Wait for database → ⏳ 
2. Create schemas    → CREATE SCHEMA IF NOT EXISTS catalog, keycloak
3. Run migrations    → catalog module migrations execute
4. Start app        → ✅ Ready!
```

**You don't need to run migration commands manually!**

## When Do You Need to Do Something?

### Only When You Modify ORM Models

If you add/change tables in `catalog/infrastructure/orm_models.py`:

```bash
cd backend
poetry run alembic -c app/modules/catalog/alembic.ini revision --autogenerate -m "Your change description"
```

Then commit the new migration file and restart the app - that's it!

## Database Structure

```
PostgreSQL Database: eshop
├── catalog schema   ← Products, catalog items, categories, brands
│   └── alembic_version (tracks catalog migrations)
└── keycloak schema  ← Authentication data (managed by Keycloak)
```

## Shell Scripts Removed

**Q: What about create-migration.sh and run-migrations.sh?**

**A:** Removed! You were right - migrations run automatically on app startup. The shell scripts were unnecessary since:
- Migrations auto-execute when app starts
- Creating new migrations uses Alembic CLI directly (rare operation)
- No need for wrapper scripts

## Key Benefits

1. **Zero Manual Work**: Migrations run automatically
2. **Modular**: Each module manages its own schema
3. **Schema Isolation**: Catalog has its own PostgreSQL schema
4. **Clean Separation**: Infrastructure (Keycloak) separated from business logic
5. **Future-Ready**: Basket and ordering can be added easily

## For Developers

### Adding a New Catalog Feature

1. **Modify ORM model**:
   ```python
   # backend/app/modules/catalog/infrastructure/orm_models.py
   class NewFeatureORM(Base):
       __tablename__ = "new_feature"
       __table_args__ = {"schema": "catalog"}  # Important!
       # ... your columns
   ```

2. **Create migration**:
   ```bash
   cd backend
   poetry run alembic -c app/modules/catalog/alembic.ini revision --autogenerate -m "Add new feature"
   ```

3. **Start app** - migration runs automatically!

### Implementing Basket/Ordering Later

When ready to implement basket or ordering:

1. Uncomment the module in `migrations.py` MODULE_CONFIGS
2. Add real ORM models to `basket/infrastructure/orm_models.py`
3. Create real migration to replace placeholder
4. Add schema to `ensure_schemas_exist()` function
5. Restart app - done!

## Documentation

- **MIGRATIONS_PER_MODULE.md**: Complete guide with troubleshooting
- **REFACTORING_SUMMARY.md**: Detailed architecture changes
- **backend/alembic/DEPRECATED.md**: Old system deprecation notice

## Common Questions

**Q: Do I need to run migrations manually?**  
A: No! They run automatically when the app starts.

**Q: What if I add a new table?**  
A: Modify the ORM model, create a migration with Alembic, restart the app.

**Q: What about basket and ordering tables?**  
A: Placeholders for now. They'll be implemented when those modules are developed.

**Q: Where are the Keycloak provisioning files?**  
A: Moved to `infra/keycloak/keycloak_setup.py`

**Q: Do schemas get created automatically?**  
A: Yes! `catalog` and `keycloak` schemas are created before migrations run.

## Quick Commands Reference

```bash
# Check current migration status
cd backend
poetry run alembic -c app/modules/catalog/alembic.ini current

# View migration history
poetry run alembic -c app/modules/catalog/alembic.ini history

# Create new migration (after modifying ORM models)
poetry run alembic -c app/modules/catalog/alembic.ini revision --autogenerate -m "description"
```

That's it! The system is designed to be automatic and require minimal manual intervention. Just develop your features and let the migration system handle the database setup! 🚀

