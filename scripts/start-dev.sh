#!/bin/bash

echo "🚀 Starting eShop in development mode..."

# Check if we're in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run from the project root."
    exit 1
fi

echo "📦 Building and starting services..."
docker-compose up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 30

echo "🔑 Setting up Keycloak..."
# Run the Keycloak setup script
if [ -f "setup-keycloak.sh" ]; then
    ./setup-keycloak.sh
else
    echo "⚠️ Keycloak setup script not found. You may need to set up users manually."
fi

echo "🔄 Running database migrations..."
docker-compose exec backend alembic upgrade head

echo "🌐 Services are starting up!"
echo ""
echo "📋 Access URLs:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Keycloak:  http://localhost:8080"
echo "  RabbitMQ:  http://localhost:15672 (guest/guest)"
echo ""
echo "👥 Test Users:"
echo "  testuser / password (User role)"
echo "  admin / password (Admin role)"
echo ""
echo "📊 Check status with: docker-compose ps"
echo "📋 View logs with: docker-compose logs -f [service]"
echo "🛑 Stop with: docker-compose down"
