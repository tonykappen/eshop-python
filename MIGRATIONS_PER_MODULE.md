# Per-Module Database Migrations Guide

## Overview

The eShop application now uses a **per-module migration system** where each module (Catalog, Basket, Ordering) manages its own database schema and migrations independently using Alembic.

## Architecture

### Module Structure

Each module has its own Alembic configuration:

```
backend/app/modules/
├── catalog/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 001_initial_migration.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   └── infrastructure/
│       └── orm_models.py
├── basket/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 001_initial_migration.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   └── infrastructure/
│       └── orm_models.py
└── ordering/
    ├── alembic/
    │   ├── versions/
    │   │   └── 001_initial_migration.py
    │   ├── env.py
    │   └── script.py.mako
    ├── alembic.ini
    └── infrastructure/
        └── orm_models.py
```

### Infrastructure Structure

External service provisioning (like Keycloak) is now organized under the `infra/` directory:

```
infra/
└── keycloak/
    ├── __init__.py
    └── keycloak_setup.py
```

## Database Schemas

Each module has its own PostgreSQL schema:

- **catalog** schema: Contains products, catalog_items, catalog_categories, catalog_brands
- **basket** schema: Contains baskets, basket_items
- **ordering** schema: Contains orders, order_items
- **keycloak** schema: Managed by Keycloak for authentication data

## How Migrations Work

### Automatic Migration Execution

Migrations are automatically run during application startup:

1. **Schema Creation**: The migration system ensures all required schemas exist before running migrations
2. **Per-Module Execution**: Each module's migrations are run independently
3. **Order**: Modules are migrated in order: catalog → basket → ordering

### Migration Process

The migration process is handled by `app/core/database/migrations.py`:

```python
# Module configurations
MODULE_CONFIGS = [
    {"name": "catalog", "path": "app/modules/catalog", "schema": "catalog"},
    {"name": "basket", "path": "app/modules/basket", "schema": "basket"},
    {"name": "ordering", "path": "app/modules/ordering", "schema": "ordering"},
]
```

### Schema Creation

Schemas are created automatically via:
- `ensure_schemas_exist()` function in `migrations.py`
- Individual module `env.py` files that create schemas before running migrations

## Creating New Migrations

### Important: Migrations Run Automatically!

**Migrations are automatically executed when the application starts**, so you typically don't need to run them manually. The system:
1. Waits for the database to be ready
2. Creates required schemas (catalog, keycloak)
3. Runs migrations for each module
4. Continues with application startup

### When You Need Manual Migration Creation

You only need to manually create migrations when you **modify ORM models**:

#### For Catalog Module:
```bash
cd backend
poetry run alembic -c app/modules/catalog/alembic.ini revision --autogenerate -m "Add new catalog feature"
```

#### For Future Modules (when implemented):
```bash
cd backend
# Basket (placeholder for now)
poetry run alembic -c app/modules/basket/alembic.ini revision --autogenerate -m "Add basket feature"

# Ordering (placeholder for now)
poetry run alembic -c app/modules/ordering/alembic.ini revision --autogenerate -m "Add ordering feature"
```

### Running Migrations Manually (Optional)

Migrations run automatically on app startup, but if you want to test them separately:

```bash
cd backend
# Run catalog migrations
poetry run alembic -c app/modules/catalog/alembic.ini upgrade head

# Check current version
poetry run alembic -c app/modules/catalog/alembic.ini current
```

## Key Features

### 1. Schema Isolation
- Each module's tables are isolated in their own PostgreSQL schema
- Prevents naming conflicts between modules
- Improves security and organization

### 2. Independent Versioning
- Each module maintains its own migration version history
- Modules can evolve independently without affecting others
- Version tables are stored in each module's schema

### 3. Automatic Schema Creation
- Schemas are automatically created if they don't exist
- No manual database setup required
- Works seamlessly with Docker deployments

### 4. Include Object Filtering
Each module's `env.py` includes an `include_object` function that ensures only tables in that module's schema are included in migrations:

```python
def include_object(object, name, type_, reflected, compare_to):
    """Filter objects to only include those in the module's schema."""
    if type_ == "table":
        return object.schema == MODULE_SCHEMA
    return True
```

## Migration Best Practices

### 1. ORM Models
- Define all tables in `infrastructure/orm_models.py` for each module
- Always specify the schema in `__table_args__`: `{"schema": "catalog"}`
- Use proper type hints with SQLAlchemy 2.0 `Mapped` types

### 2. Foreign Keys Across Schemas
When referencing tables from other schemas:
```python
sa.ForeignKeyConstraint(['basket_id'], ['basket.baskets.id'])
```

### 3. Testing Migrations
- Test migrations in a development environment first
- Verify both upgrade and downgrade operations work
- Check that schema creation happens before table creation

### 4. Version Control
- Always commit migration files to version control
- Never modify existing migration files after they've been applied
- Use descriptive migration messages

## Troubleshooting

### Schema Not Found Error
If you get "schema does not exist" errors:
- Check that `ensure_schemas_exist()` is running before migrations
- Verify the schema name matches in `orm_models.py` and `env.py`

### Migration Not Found
If Alembic can't find migrations:
- Verify the `alembic.ini` path is correct
- Check that `script_location` in `alembic.ini` points to the `alembic` directory
- Ensure `prepend_sys_path` is set correctly

### Table Already Exists
If you get "table already exists" errors:
- Check the alembic_version table in the module's schema
- Run: `SELECT * FROM catalog.alembic_version;`
- If empty, you may need to stamp the current version: 
  ```bash
  poetry run alembic -c app/modules/catalog/alembic.ini stamp head
  ```

## Comparison with Previous System

### Before (Monolithic)
- Single `alembic` directory at backend root
- All tables in one or mixed schemas
- Single version history for entire database
- Manual schema creation via Docker scripts

### After (Per-Module)
- Each module has its own `alembic` configuration
- Tables organized by schema per module
- Independent version history per module
- Automatic schema creation via Alembic

## Infrastructure Services

### Keycloak Setup
Keycloak provisioning has been moved to `infra/keycloak/`:

```python
from infra.keycloak.keycloak_setup import setup_keycloak_async

# Setup is automatically called during application startup
```

The Keycloak schema is created automatically alongside module schemas, but Keycloak manages its own tables internally.

## Docker Integration

The Docker setup has been updated to remove schema creation from `ensure-schemas.sh`:

**Before:**
```bash
# Created schemas manually in SQL script
CREATE SCHEMA IF NOT EXISTS keycloak;
CREATE SCHEMA IF NOT EXISTS catalog;
```

**After:**
```bash
# Only ensures PostgreSQL is ready
# Schemas created by Alembic migrations
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)

