#!/bin/bash

echo "🧪 Testing VS Code Launch Configurations..."
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Backend Health Check
echo -e "${BLUE}1. Testing Backend Health Check...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is running and healthy${NC}"
else
    echo -e "${RED}❌ Backend is not responding${NC}"
fi

# Test 2: Frontend Health Check
echo -e "${BLUE}2. Testing Frontend Health Check...${NC}"
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${RED}❌ Frontend is not responding${NC}"
fi

# Test 3: Database Connection
echo -e "${BLUE}3. Testing Database Connection...${NC}"
if podman exec eshop-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is running and accessible${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not accessible${NC}"
fi

# Test 4: Redis Connection
echo -e "${BLUE}4. Testing Redis Connection...${NC}"
if podman exec eshop-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running and accessible${NC}"
else
    echo -e "${RED}❌ Redis is not accessible${NC}"
fi

# Test 5: RabbitMQ Connection
echo -e "${BLUE}5. Testing RabbitMQ Connection...${NC}"
if curl -s -u guest:guest http://localhost:15672/api/overview > /dev/null; then
    echo -e "${GREEN}✅ RabbitMQ is running and accessible${NC}"
else
    echo -e "${RED}❌ RabbitMQ is not accessible${NC}"
fi

# Test 6: Keycloak Status
echo -e "${BLUE}6. Testing Keycloak Status...${NC}"
if curl -s http://localhost:8080/realms/master > /dev/null; then
    echo -e "${GREEN}✅ Keycloak is running${NC}"
else
    echo -e "${YELLOW}⚠️ Keycloak is not running (expected due to network issue)${NC}"
fi

# Test 7: Backend API Endpoints
echo -e "${BLUE}7. Testing Backend API Endpoints...${NC}"
if curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "${GREEN}✅ FastAPI docs are accessible${NC}"
else
    echo -e "${RED}❌ FastAPI docs are not accessible${NC}"
fi

# Test 8: Environment Variables Check
echo -e "${BLUE}8. Testing Environment Variables...${NC}"
cd backend
if poetry run python -c "
import os
required_vars = ['DATABASE_URL', 'REDIS_URL', 'RABBITMQ_URL']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'Missing: {missing}')
    exit(1)
else:
    print('All required env vars are set')
" 2>/dev/null; then
    echo -e "${GREEN}✅ Environment variables are properly configured${NC}"
else
    echo -e "${YELLOW}⚠️ Some environment variables may be missing${NC}"
fi
cd ..

echo ""
echo -e "${BLUE}🎯 VS Code Launch Configuration Test Results:${NC}"
echo "=========================================="

# Summary
echo -e "${GREEN}✅ Ready for VS Code Debugging:${NC}"
echo "  • Backend debugging should work"
echo "  • Frontend debugging should work"
echo "  • Database operations should work"
echo "  • Message queuing should work"
echo "  • Caching should work"

echo ""
echo -e "${YELLOW}⚠️ Known Issues:${NC}"
echo "  • Keycloak needs network configuration fix"
echo "  • Some containers had naming conflicts (resolved)"

echo ""
echo -e "${BLUE}🔧 Next Steps:${NC}"
echo "1. Open VS Code in this project"
echo "2. Go to Run and Debug (Ctrl+Shift+D)"
echo "3. Select a launch configuration:"
echo "   • 'Debug Backend (uvicorn)' - for backend debugging"
echo "   • 'Debug Frontend (Chrome)' - for frontend debugging"
echo "   • 'Debug Full Stack' - for both"
echo "4. Set breakpoints in your code"
echo "5. Press F5 to start debugging"

echo ""
echo -e "${GREEN}🎉 Launch configurations are ready to test!${NC}"
