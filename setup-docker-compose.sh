#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up eShop with Docker Compose...${NC}"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose is available${NC}"

# Stop any existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose down -v 2>/dev/null || true

# Build and start services
echo -e "${BLUE}🔨 Building and starting services...${NC}"
if docker-compose up --build -d; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    exit 1
fi

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Check service status
echo -e "${BLUE}📊 Service Status:${NC}"
docker-compose ps

# Wait for Keycloak to be fully initialized
echo -e "${BLUE}⏳ Waiting for Keycloak to be fully initialized...${NC}"
sleep 30

# Check if Keycloak is accessible
echo -e "${BLUE}🔍 Checking Keycloak accessibility...${NC}"
if curl -s http://localhost:8080/realms/eshop > /dev/null; then
    echo -e "${GREEN}✅ Keycloak is accessible${NC}"
else
    echo -e "${YELLOW}⚠️ Keycloak not ready yet, waiting...${NC}"
    sleep 30
fi

# Run Keycloak setup
echo -e "${BLUE}🔐 Setting up Keycloak...${NC}"
if [ -f "./setup-keycloak.sh" ]; then
    ./setup-keycloak.sh
else
    echo -e "${YELLOW}⚠️ Keycloak setup script not found${NC}"
fi

# Create users using our script
echo -e "${BLUE}👥 Creating users...${NC}"
if [ -f "./create-users.sh" ]; then
    ./create-users.sh
else
    echo -e "${YELLOW}⚠️ User creation script not found${NC}"
fi

# Test the application
echo -e "${BLUE}🧪 Testing application...${NC}"
sleep 10

# Test health endpoints
echo -e "${BLUE}🔍 Testing health endpoints...${NC}"
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

if curl -s http://localhost:3000 | grep -q "html"; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend health check failed${NC}"
fi

echo -e "${GREEN}🎉 Docker Compose setup complete!${NC}"

echo -e "${BLUE}📋 Access Points:${NC}"
echo -e "  • Frontend: http://localhost:3000"
echo -e "  • Backend API: http://localhost:8000"
echo -e "  • API Documentation: http://localhost:8000/docs"
echo -e "  • Health Check: http://localhost:8000/health/detailed"
echo -e "  • Keycloak Admin: http://localhost:8080/admin/ (admin/admin)"
echo -e "  • RabbitMQ Management: http://localhost:15672 (guest/guest)"

echo -e "${BLUE}👥 Test Users:${NC}"
echo -e "  • user/password (User role)"
echo -e "  • manager/password (Manager role)"
echo -e "  • adminuser/password (Admin role)"
echo -e "  • testuser/password (User role)"

echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo -e "  • View logs: docker-compose logs -f"
echo -e "  • Stop services: docker-compose down"
echo -e "  • Restart services: docker-compose restart"
echo -e "  • Rebuild: docker-compose up --build -d"

echo -e "${GREEN}✅ Setup complete!${NC}"
