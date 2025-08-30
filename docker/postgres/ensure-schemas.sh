#!/bin/bash
set -e

echo "🔧 Ensuring database schemas exist..."

# Wait for PostgreSQL to be ready
until pg_isready -U postgres -d eshop; do
  echo "⏳ Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Connect to database and ensure schemas exist
psql -U postgres -d eshop <<-EOSQL
  -- Create Keycloak schema (safe to run multiple times)
  CREATE SCHEMA IF NOT EXISTS keycloak;
  
  -- Create catalog schema (safe to run multiple times)
  CREATE SCHEMA IF NOT EXISTS catalog;
  
  -- Create extensions if needed
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  
  -- Set timezone
  SET timezone = 'UTC';
  
  -- Verify schemas exist
  SELECT '✅ Schema ' || nspname || ' exists' as status 
  FROM pg_namespace 
  WHERE nspname IN ('catalog', 'keycloak', 'public');
EOSQL

echo "✅ Database schemas ensured successfully!"
