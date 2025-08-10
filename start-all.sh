#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting eShop Full Stack Application...${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s $url > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    echo -e "${RED}❌ $service_name failed to start after $((max_attempts * 2)) seconds${NC}"
    return 1
}

# Step 1: Start infrastructure services (PostgreSQL, Redis, RabbitMQ, Keycloak)
echo -e "${BLUE}📦 Step 1: Starting infrastructure services...${NC}"
if [ -f "./setup-podman.sh" ]; then
    ./setup-podman.sh
else
    echo -e "${RED}❌ setup-podman.sh not found${NC}"
    exit 1
fi

# Wait for Keycloak to be fully ready
wait_for_service "http://localhost:8080/realms/eshop" "Keycloak"

# Step 2: Start Backend API
echo -e "${BLUE}🔧 Step 2: Starting Backend API...${NC}"

# Kill any existing backend processes
echo -e "${YELLOW}🧹 Cleaning up existing backend processes...${NC}"
if check_port 8000; then
    echo -e "${YELLOW}Port 8000 is in use, stopping existing processes...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start backend in background
echo -e "${BLUE}🚀 Starting FastAPI backend...${NC}"
cd backend
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
wait_for_service "http://localhost:8000/health" "Backend API"

# Step 3: Start Frontend
echo -e "${BLUE}🌐 Step 3: Starting Frontend...${NC}"

# Clean up existing frontend containers
podman rm -f eshop-frontend 2>/dev/null || true

# Build and start frontend
cd frontend
echo -e "${BLUE}🔨 Building frontend container...${NC}"
if podman build -t eshop-frontend .; then
    echo -e "${GREEN}✅ Frontend built successfully${NC}"
else
    echo -e "${RED}❌ Frontend build failed${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Starting frontend container...${NC}"
if podman run -d --name eshop-frontend -p 3000:80 eshop-frontend; then
    echo -e "${GREEN}✅ Frontend started successfully${NC}"
else
    echo -e "${RED}❌ Frontend failed to start${NC}"
    exit 1
fi
cd ..

# Wait for frontend to be ready
wait_for_service "http://localhost:3000" "Frontend"

# Step 4: Display status and URLs
echo -e "\n${GREEN}🎉 eShop Full Stack Application Started Successfully!${NC}\n"

echo -e "${BLUE}📋 Service Status:${NC}"
echo -e "  ${GREEN}✅ PostgreSQL:${NC} $(podman ps --filter name=eshop-postgres --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
echo -e "  ${GREEN}✅ Redis:${NC} $(podman ps --filter name=eshop-redis --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
echo -e "  ${GREEN}✅ RabbitMQ:${NC} $(podman ps --filter name=eshop-rabbitmq --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
echo -e "  ${GREEN}✅ Keycloak:${NC} $(podman ps --filter name=eshop-keycloak --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
echo -e "  ${GREEN}✅ Backend API:${NC} Running (PID: $BACKEND_PID)"
echo -e "  ${GREEN}✅ Frontend:${NC} $(podman ps --filter name=eshop-frontend --format '{{.Status}}' 2>/dev/null || echo 'Not running')"

echo -e "\n${BLUE}🌐 Access URLs:${NC}"
echo -e "  ${GREEN}• Frontend (Login):${NC} http://localhost:3000"
echo -e "  ${GREEN}• Backend API:${NC} http://localhost:8000"
echo -e "  ${GREEN}• API Documentation:${NC} http://localhost:8000/docs"
echo -e "  ${GREEN}• Health Checks:${NC} http://localhost:8000/health/detailed"
echo -e "  ${GREEN}• Keycloak Admin:${NC} http://localhost:8080/admin (admin/admin)"
echo -e "  ${GREEN}• RabbitMQ Management:${NC} http://localhost:15672 (guest/guest)"

echo -e "\n${BLUE}👥 Test Users:${NC}"
echo -e "  ${GREEN}• Admin:${NC} admin/password (Full access)"
echo -e "  ${GREEN}• Manager:${NC} manager/password (Edit access)"
echo -e "  ${GREEN}• User:${NC} user/password (Read-only access)"

echo -e "\n${BLUE}🔧 Useful Commands:${NC}"
echo -e "  ${YELLOW}• View backend logs:${NC} tail -f backend.log"
echo -e "  ${YELLOW}• View frontend logs:${NC} podman logs eshop-frontend"
echo -e "  ${YELLOW}• Stop all services:${NC} ./stop-all.sh"
echo -e "  ${YELLOW}• Check health:${NC} curl http://localhost:8000/health/detailed"

echo -e "\n${GREEN}🎯 Ready to test! Open http://localhost:3000 in your browser${NC}"
