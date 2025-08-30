#!/bin/bash
set -e

# Start PostgreSQL in the background
echo "🚀 Starting PostgreSQL..."
exec /usr/local/bin/docker-entrypoint.sh postgres &

# Wait for PostgreSQL to start
sleep 10

# Run our schema creation script
echo "🔧 Running schema creation..."
/usr/local/bin/ensure-schemas.sh

# Wait for the PostgreSQL process
wait $!
