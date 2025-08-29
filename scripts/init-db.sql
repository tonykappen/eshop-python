-- Initialize eShop database
-- This script runs when PostgreSQL container starts

-- Create Keycloak database
CREATE DATABASE keycloak;

-- Create test database
CREATE DATABASE eshop_test;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE eshop TO postgres;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO postgres;
GRANT ALL PRIVILEGES ON DATABASE eshop_test TO postgres;

-- Create extensions if needed
\c eshop;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c eshop_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';
