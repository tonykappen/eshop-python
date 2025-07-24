#!/bin/bash

echo "🚀 Setting up eShop Modular Monolith with Docker..."

# Check if Docker is running and accessible
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Build the application image
echo "🔨 Building application image..."
docker build -t eshop-python . 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Application image built successfully"
else
    echo "❌ Failed to build application image"
    echo "   This might be due to Docker authentication requirements."
    echo "   Please sign in to Docker Desktop and try again."
    exit 1
fi

# Start the services
echo "🐳 Starting services with docker-compose..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Services started successfully"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "🌐 Application will be available at: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo ""
    echo "📦 Services:"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo "  - RabbitMQ: localhost:5672"
    echo "  - RabbitMQ Management: http://localhost:15672"
    echo ""
    echo "🛑 To stop services: docker-compose down"
    echo "📋 To view logs: docker-compose logs -f"
else
    echo "❌ Failed to start services"
    exit 1
fi 