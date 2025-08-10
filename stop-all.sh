#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping eShop Full Stack Application...${NC}"

# Stop Backend API
echo -e "${YELLOW}🔧 Stopping Backend API...${NC}"
if lsof -ti:8000 > /dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ Backend API stopped${NC}"
else
    echo -e "${YELLOW}⚠️ No backend process found on port 8000${NC}"
fi

# Stop Frontend
echo -e "${YELLOW}🌐 Stopping Frontend...${NC}"
if podman ps --filter name=eshop-frontend --format '{{.Names}}' | grep -q eshop-frontend; then
    podman stop eshop-frontend 2>/dev/null || true
    podman rm eshop-frontend 2>/dev/null || true
    echo -e "${GREEN}✅ Frontend stopped${NC}"
else
    echo -e "${YELLOW}⚠️ Frontend container not running${NC}"
fi

# Stop Infrastructure Services
echo -e "${YELLOW}📦 Stopping Infrastructure Services...${NC}"

services=("eshop-keycloak" "eshop-rabbitmq" "eshop-redis" "eshop-postgres")

for service in "${services[@]}"; do
    if podman ps --filter name=$service --format '{{.Names}}' | grep -q $service; then
        echo -e "${YELLOW}Stopping $service...${NC}"
        podman stop $service 2>/dev/null || true
        podman rm $service 2>/dev/null || true
        echo -e "${GREEN}✅ $service stopped${NC}"
    else
        echo -e "${YELLOW}⚠️ $service not running${NC}"
    fi
done

# Clean up network
echo -e "${YELLOW}🧹 Cleaning up network...${NC}"
podman network rm eshop-network 2>/dev/null || true

# Clean up log files
if [ -f "backend.log" ]; then
    rm backend.log
    echo -e "${GREEN}✅ Cleaned up log files${NC}"
fi

echo -e "\n${GREEN}🎉 All services stopped successfully!${NC}"

echo -e "\n${BLUE}📋 Final Status:${NC}"
echo -e "  ${GREEN}• All containers stopped and removed${NC}"
echo -e "  ${GREEN}• Network cleaned up${NC}"
echo -e "  ${GREEN}• Log files removed${NC}"

echo -e "\n${BLUE}🚀 To start again, run: ./start-all.sh${NC}"
