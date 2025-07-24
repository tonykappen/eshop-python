#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up eShop Modular Monolith with Podman...${NC}"

# Check if Podman is running
if ! podman info > /dev/null 2>&1; then
    echo -e "${RED}❌ Podman is not running${NC}"
    echo "Please run: podman machine start"
    exit 1
fi

echo -e "${GREEN}✅ Podman is running${NC}"

# Build the application image
echo -e "${BLUE}🔨 Building application image...${NC}"
if podman build -t eshop-modular-monolith .; then
    echo -e "${GREEN}✅ Application image built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build application image${NC}"
    exit 1
fi

# Start the services using docker-compose with Podman backend
echo -e "${BLUE}🚀 Starting services...${NC}"
if DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock" docker-compose up -d; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    echo "Trying alternative approach..."
    
    # Alternative: Start services individually with Podman
    echo -e "${BLUE}🔄 Starting services individually...${NC}"
    
    # Start PostgreSQL
    podman run -d --name eshop-postgres \
        -e POSTGRES_DB=eshop \
        -e POSTGRES_USER=eshop_user \
        -e POSTGRES_PASSWORD=eshop_password \
        -p 5432:5432 \
        postgres:15
    
    # Start Redis
    podman run -d --name eshop-redis \
        -p 6379:6379 \
        redis:7
    
    # Start RabbitMQ
    podman run -d --name eshop-rabbitmq \
        -e RABBITMQ_DEFAULT_USER=guest \
        -e RABBITMQ_DEFAULT_PASS=guest \
        -p 5672:5672 \
        -p 15672:15672 \
        rabbitmq:3-management
    
    echo -e "${GREEN}✅ Services started individually${NC}"
fi

# Wait a moment for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check service status
echo -e "${BLUE}📊 Service Status:${NC}"
echo -e "${YELLOW}PostgreSQL:${NC} $(podman ps --filter name=eshop-postgres --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
echo -e "${YELLOW}Redis:${NC} $(podman ps --filter name=eshop-redis --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
echo -e "${YELLOW}RabbitMQ:${NC} $(podman ps --filter name=eshop-rabbitmq --format '{{.Status}}' 2>/dev/null || echo 'Not running')"

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo -e "${BLUE}📋 Access Points:${NC}"
echo -e "  • Application: http://localhost:8000"
echo -e "  • API Docs: http://localhost:8000/docs"
echo -e "  • PostgreSQL: localhost:5432"
echo -e "  • Redis: localhost:6379"
echo -e "  • RabbitMQ Management: http://localhost:15672 (guest/guest)"

echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo -e "  • View logs: podman logs <container-name>"
echo -e "  • Stop services: podman stop eshop-postgres eshop-redis eshop-rabbitmq"
echo -e "  • Remove containers: podman rm eshop-postgres eshop-redis eshop-rabbitmq" 