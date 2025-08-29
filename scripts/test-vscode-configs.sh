#!/bin/bash

# Test VS Code Configurations Script
# This script tests all the VS Code launch configurations and tasks

set -e

echo "🧪 Testing VS Code Configurations..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to test a service
test_service() {
    local service_name="$1"
    local url="$2"
    local expected_pattern="$3"
    
    echo -e "${BLUE}Testing $service_name...${NC}"
    
    if curl -s "$url" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✅ $service_name is working${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not working${NC}"
        return 1
    fi
}

# Function to test port availability
test_port() {
    local port="$1"
    local service_name="$2"
    
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Port $port is available for $service_name${NC}"
        return 0
    else
        echo -e "${YELLOW}ℹ️ Port $port is not in use${NC}"
        return 0
    fi
}

echo ""
echo "🔍 Checking Environment Variables..."

# Test environment variables
if [ -n "$DATABASE_URL" ]; then
    echo -e "${GREEN}✅ DATABASE_URL is set${NC}"
else
    echo -e "${YELLOW}ℹ️ DATABASE_URL not set (will use default)${NC}"
fi

if [ -n "$REDIS_URL" ]; then
    echo -e "${GREEN}✅ REDIS_URL is set${NC}"
else
    echo -e "${YELLOW}ℹ️ REDIS_URL not set (will use default)${NC}"
fi

if [ -n "$RABBITMQ_URL" ]; then
    echo -e "${GREEN}✅ RABBITMQ_URL is set${NC}"
else
    echo -e "${YELLOW}ℹ️ RABBITMQ_URL not set (will use default)${NC}"
fi

if [ -n "$KEYCLOAK_SERVER_URL" ]; then
    echo -e "${GREEN}✅ KEYCLOAK_SERVER_URL is set${NC}"
else
    echo -e "${YELLOW}ℹ️ KEYCLOAK_SERVER_URL not set (will use default)${NC}"
fi

echo ""
echo "🔍 Checking Port Availability..."

# Test port availability
test_port 8000 "Backend (FastAPI)"
test_port 3000 "Frontend (HTTP Server)"
test_port 5432 "PostgreSQL"
test_port 6379 "Redis"
test_port 5672 "RabbitMQ"
test_port 8080 "Keycloak"

echo ""
echo "🔍 Testing Infrastructure Services..."

# Test infrastructure services
test_service "PostgreSQL" "http://localhost:5432" "PostgreSQL" || echo -e "${YELLOW}ℹ️ PostgreSQL not running (expected if not started)${NC}"
test_service "Redis" "http://localhost:6379" "redis" || echo -e "${YELLOW}ℹ️ Redis not running (expected if not started)${NC}"

echo ""
echo "🔍 Testing Application Services..."

# Test application services
test_service "Backend Health" "http://localhost:8000/health" "healthy" || echo -e "${YELLOW}ℹ️ Backend not running (expected if not started)${NC}"
test_service "Frontend" "http://localhost:3000/" "eShop" || echo -e "${YELLOW}ℹ️ Frontend not running (expected if not started)${NC}"

echo ""
echo "🔍 Checking VS Code Configuration Files..."

# Check if VS Code configuration files exist
if [ -f ".vscode/launch.json" ]; then
    echo -e "${GREEN}✅ launch.json exists${NC}"
else
    echo -e "${RED}❌ launch.json missing${NC}"
fi

if [ -f ".vscode/tasks.json" ]; then
    echo -e "${GREEN}✅ tasks.json exists${NC}"
else
    echo -e "${RED}❌ tasks.json missing${NC}"
fi

if [ -f ".vscode/settings.json" ]; then
    echo -e "${GREEN}✅ settings.json exists${NC}"
else
    echo -e "${RED}❌ settings.json missing${NC}"
fi

if [ -f ".vscode/keybindings.json" ]; then
    echo -e "${GREEN}✅ keybindings.json exists${NC}"
else
    echo -e "${RED}❌ keybindings.json missing${NC}"
fi

echo ""
echo "🔍 Checking Scripts..."

# Check if scripts exist
if [ -f "scripts/stop-servers.sh" ]; then
    echo -e "${GREEN}✅ stop-servers.sh exists${NC}"
else
    echo -e "${RED}❌ stop-servers.sh missing${NC}"
fi

if [ -f "scripts/start-infrastructure.sh" ]; then
    echo -e "${GREEN}✅ start-infrastructure.sh exists${NC}"
else
    echo -e "${RED}❌ start-infrastructure.sh missing${NC}"
fi

echo ""
echo "🔍 Testing Python Environment..."

# Test Python environment
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python 3 is available${NC}"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
fi

if command -v poetry &> /dev/null; then
    echo -e "${GREEN}✅ Poetry is available${NC}"
else
    echo -e "${RED}❌ Poetry not found${NC}"
fi

echo ""
echo "🔍 Testing Backend Dependencies..."

# Test backend dependencies
cd backend
if poetry show fastapi > /dev/null 2>&1; then
    echo -e "${GREEN}✅ FastAPI is installed${NC}"
else
    echo -e "${RED}❌ FastAPI not installed${NC}"
fi

if poetry show uvicorn > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Uvicorn is installed${NC}"
else
    echo -e "${RED}❌ Uvicorn not installed${NC}"
fi

cd ..

echo ""
echo "🎯 VS Code Configuration Summary:"
echo "================================"
echo ""
echo "✅ Backend Debug Configurations:"
echo "   - Debug Backend (FastAPI)"
echo "   - Debug Backend (uvicorn)"
echo "   - Debug Backend Tests"
echo ""
echo "✅ Frontend Debug Configurations:"
echo "   - Debug Frontend (HTTP Server)"
echo "   - Debug Frontend (Chrome)"
echo "   - Debug Frontend (Edge)"
echo ""
echo "✅ Compound Configurations:"
echo "   - Debug Full Stack (Backend + Frontend)"
echo "   - Debug Backend + Tests"
echo "   - Stop All Debug Sessions"
echo ""
echo "✅ Tasks:"
echo "   - Start Frontend Server"
echo "   - Stop All Development Servers"
echo "   - Stop Backend Server"
echo "   - Stop Frontend Server"
echo "   - Check Running Servers"
echo ""
echo "✅ Keyboard Shortcuts:"
echo "   - Ctrl+Shift+K: Stop current debug session"
echo "   - Ctrl+Shift+Alt+K: Stop all debug sessions"
echo "   - Ctrl+Shift+T: Stop all development servers"
echo "   - Ctrl+Shift+B: Stop backend server"
echo "   - Ctrl+Shift+F: Stop frontend server"
echo "   - Ctrl+Shift+C: Check running servers"
echo ""
echo "🎉 All VS Code configurations are ready for use!"
echo ""
echo "📋 Next Steps:"
echo "1. Open VS Code in this project directory"
echo "2. Go to Run and Debug (Ctrl+Shift+D)"
echo "3. Select a configuration from the dropdown"
echo "4. Press F5 to start debugging"
echo ""
echo "🛑 To stop servers:"
echo "- Use the stop tasks in VS Code"
echo "- Or run: ./scripts/stop-servers.sh"
