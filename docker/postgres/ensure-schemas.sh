#!/bin/bash
set -e

echo "🔧 Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be ready
until pg_isready -U postgres -d eshop; do
  echo "⏳ Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Basic database setup - create extensions
psql -U postgres -d eshop <<-EOSQL
  -- Create extensions if needed
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  
  -- Set timezone
  SET timezone = 'UTC';
EOSQL

echo "✅ PostgreSQL is ready!"
echo "ℹ️  Note: Database schemas will be created by Alembic migrations"
