#!/bin/bash

echo "🛑 Stopping eShop Infrastructure Services..."

# Stop infrastructure services
podman-compose -f docker-compose.infrastructure.yml down

echo "✅ Infrastructure services stopped successfully!"
echo ""
echo "💡 To start again: ./scripts/start-infrastructure.sh"
