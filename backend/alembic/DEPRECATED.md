# DEPRECATED: Monolithic Alembic Configuration

**⚠️ This directory and configuration are deprecated as of October 10, 2025.**

## What Changed?

The application has migrated from a monolithic Alembic configuration to a **per-module migration system**.

### Old Structure (Deprecated)
```
backend/
└── alembic/
    ├── versions/
    │   └── 19c94aa27f18_initial_migration.py
    ├── env.py
    └── script.py.mako
```

### New Structure (Active)
```
backend/app/modules/
├── catalog/alembic/
├── basket/alembic/
└── ordering/alembic/
```

## Migration Path

If you have an existing database using the old monolithic migrations:

### Option 1: Fresh Start (Recommended for Development)
1. Drop the database and recreate it
2. Run the application - new per-module migrations will execute automatically

### Option 2: Migration (For Production)
1. Create a backup of your database
2. Mark the old migration as applied:
   ```sql
   -- Check current version
   SELECT version_num FROM public.alembic_version;
   
   -- If it shows '19c94aa27f18', you need to migrate
   ```

3. Stamp the new per-module migrations as complete:
   ```bash
   cd backend
   poetry run alembic -c app/modules/catalog/alembic.ini stamp head
   poetry run alembic -c app/modules/basket/alembic.ini stamp head
   poetry run alembic -c app/modules/ordering/alembic.ini stamp head
   ```

4. Update the version tracking:
   ```sql
   -- Delete old version table (backup first!)
   DROP TABLE IF EXISTS public.alembic_version;
   ```

## Why the Change?

### Benefits of Per-Module Migrations

1. **Modularity**: Each module manages its own database schema independently
2. **Schema Isolation**: Each module uses its own PostgreSQL schema (catalog, basket, ordering)
3. **Independent Evolution**: Modules can evolve their schemas without affecting others
4. **Better Organization**: Clear separation of concerns matches module boundaries
5. **Easier Testing**: Can test module migrations in isolation

### Key Differences

| Aspect | Old (Monolithic) | New (Per-Module) |
|--------|------------------|------------------|
| Configuration | Single `alembic.ini` | One per module |
| Schemas | Mixed or single | One per module |
| Version History | Single | One per module |
| Schema Creation | Manual (Docker script) | Automatic (in migrations) |

## Documentation

See the full migration guide: `/MIGRATIONS_PER_MODULE.md`

## Questions?

If you encounter issues migrating from the old system, please refer to the troubleshooting section in `MIGRATIONS_PER_MODULE.md`.

