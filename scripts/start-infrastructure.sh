#!/bin/bash

echo "🚀 Starting eShop Infrastructure Services..."

# Check if Podman is running
if ! podman info > /dev/null 2>&1; then
    echo "❌ Podman is not running. Please run: podman machine start"
    exit 1
fi

echo "✅ Podman is running"

# Start infrastructure services
echo "🐳 Starting PostgreSQL, Redis, RabbitMQ, and Keycloak..."
podman-compose -f docker-compose.infrastructure.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Service Status:"
podman-compose -f docker-compose.infrastructure.yml ps

echo ""
echo "✅ Infrastructure services started successfully!"
echo ""
echo "📋 Access Points:"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis: localhost:6379"
echo "  • RabbitMQ: localhost:5672"
echo "  • RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "  • Keycloak Admin: http://localhost:8080 (admin/admin)"
echo ""
echo "🔧 Next Steps:"
echo "  1. Run backend locally: cd backend && poetry run uvicorn app.main:app --reload"
echo "  2. Run frontend locally: cd frontend && python -m http.server 3000"
echo "  3. Or use VS Code debug configurations"
echo ""
echo "🛑 To stop services: podman-compose -f docker-compose.infrastructure.yml down"
