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

# Get the correct DOCKER_HOST path
DOCKER_HOST_PATH=$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}' 2>/dev/null || echo "unix:///var/folders/ns/vgfzlb8n5zz35w93gh8khb400000gp/T/podman/podman-machine-default-api.sock")

if DOCKER_HOST="$DOCKER_HOST_PATH" docker-compose up -d; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    echo "Trying alternative approach..."
    
    # Alternative: Start services individually with Podman
    echo -e "${BLUE}🔄 Starting services individually...${NC}"
    
    # Clean up existing containers
    echo -e "${BLUE}🧹 Cleaning up existing containers...${NC}"
    podman rm -f eshop-postgres eshop-redis eshop-rabbitmq eshop-keycloak 2>/dev/null || true
    
    # Create network for services
    podman network create eshop-network 2>/dev/null || true
    
    # Start PostgreSQL
    echo -e "${BLUE}🗄️ Starting PostgreSQL...${NC}"
    podman run -d --name eshop-postgres \
        --network eshop-network \
        -e POSTGRES_DB=eshop \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -p 5432:5432 \
        postgres:15
    
    # Start Redis
    echo -e "${BLUE}🔴 Starting Redis...${NC}"
    podman run -d --name eshop-redis \
        --network eshop-network \
        -p 6379:6379 \
        redis:7
    
    # Start RabbitMQ
    echo -e "${BLUE}🐰 Starting RabbitMQ...${NC}"
    podman run -d --name eshop-rabbitmq \
        --network eshop-network \
        -e RABBITMQ_DEFAULT_USER=guest \
        -e RABBITMQ_DEFAULT_PASS=guest \
        -p 5672:5672 \
        -p 15672:15672 \
        rabbitmq:3-management
    
    # Start Keycloak (initial start - will be restarted after DB setup)
    echo -e "${BLUE}🔐 Starting Keycloak (initial)...${NC}"
    podman run -d --name eshop-keycloak \
        --network eshop-network \
        -e KEYCLOAK_ADMIN=admin \
        -e KEYCLOAK_ADMIN_PASSWORD=admin \
        -e KC_DB=postgres \
        -e KC_DB_URL=jdbc:postgresql://eshop-postgres:5432/keycloak \
        -e KC_DB_USERNAME=postgres \
        -e KC_DB_PASSWORD=postgres \
        -p 8080:8080 \
        quay.io/keycloak/keycloak:latest start-dev
    
    echo -e "${GREEN}✅ Services started individually${NC}"
    
    # Wait for PostgreSQL to be ready and create Keycloak database
    echo -e "${BLUE}⏳ Waiting for PostgreSQL to be ready...${NC}"
    sleep 10
    
    # Create Keycloak database
    echo -e "${BLUE}🗄️ Creating Keycloak database...${NC}"
    if podman exec eshop-postgres psql -U postgres -c "CREATE DATABASE keycloak;" 2>/dev/null; then
        echo -e "${GREEN}✅ Keycloak database created${NC}"
    else
        echo -e "${YELLOW}⚠️ Keycloak database already exists or creation failed${NC}"
    fi
    
    # Start Keycloak after database is ready
    echo -e "${BLUE}🔐 Starting Keycloak...${NC}"
    # Remove existing container if it exists
    podman rm -f eshop-keycloak 2>/dev/null || true
    
    podman run -d --name eshop-keycloak \
        --network eshop-network \
        -e KEYCLOAK_ADMIN=admin \
        -e KEYCLOAK_ADMIN_PASSWORD=admin \
        -e KC_DB=postgres \
        -e KC_DB_URL=jdbc:postgresql://eshop-postgres:5432/keycloak \
        -e KC_DB_USERNAME=postgres \
        -e KC_DB_PASSWORD=postgres \
        -p 8080:8080 \
        quay.io/keycloak/keycloak:latest start-dev
    
    echo -e "${GREEN}✅ Keycloak started${NC}"
fi

# Wait a moment for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Additional wait specifically for Keycloak to fully initialize
echo -e "${BLUE}⏳ Waiting for Keycloak to fully initialize (this may take 1-2 minutes)...${NC}"
sleep 30

# Check service status
echo -e "${BLUE}📊 Service Status:${NC}"
echo -e "${YELLOW}PostgreSQL:${NC} $(podman ps --filter name=eshop-postgres --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
echo -e "${YELLOW}Redis:${NC} $(podman ps --filter name=eshop-redis --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
echo -e "${YELLOW}RabbitMQ:${NC} $(podman ps --filter name=eshop-rabbitmq --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
echo -e "${YELLOW}Keycloak:${NC} $(podman ps --filter name=eshop-keycloak --format '{{.Status}}' 2>/dev/null || echo 'Not running')"

echo -e "${GREEN}🎉 Setup complete!${NC}"

# Set up Keycloak
echo -e "${BLUE}🔐 Setting up Keycloak...${NC}"
if [ -f "./setup-keycloak.sh" ]; then
    ./setup-keycloak.sh
else
    echo -e "${YELLOW}⚠️ Keycloak setup script not found${NC}"
fi

echo -e "${BLUE}📋 Access Points:${NC}"
echo -e "  • Application: http://localhost:8000"
echo -e "  • API Docs: http://localhost:8000/docs"
echo -e "  • Health Checks: http://localhost:8000/health/detailed"
echo -e "  • PostgreSQL: localhost:5432"
echo -e "  • Redis: localhost:6379"
echo -e "  • RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo -e "  • Keycloak Admin: http://localhost:8080 (admin/admin)"

echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo -e "  • View logs: podman logs <container-name>"
echo -e "  • Stop services: podman stop eshop-postgres eshop-redis eshop-rabbitmq eshop-keycloak"
echo -e "  • Remove containers: podman rm eshop-postgres eshop-redis eshop-rabbitmq eshop-keycloak"
echo -e "  • Test health: curl http://localhost:8000/health/detailed" 