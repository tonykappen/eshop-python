#!/bin/bash

echo "🚀 Starting eShop with Docker Compose..."

# Start services
docker-compose up -d

echo "✅ Services started!"
echo ""
echo "📋 Access Points:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Keycloak Admin: http://localhost:8080/admin/ (admin/admin)"
echo ""
echo "🔧 Commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop: docker-compose down"
echo "  • Restart: docker-compose restart"
