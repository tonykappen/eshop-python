#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Debugging Docker build issues...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "Please start Docker Desktop or Docker daemon"
    exit 1
fi

echo -e "${GREEN}✅ Docker daemon is running${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ docker-compose.yml not found. Please run this script from the project root.${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Checking backend dependencies...${NC}"

# Check pyproject.toml
if [ ! -f "backend/pyproject.toml" ]; then
    echo -e "${RED}❌ backend/pyproject.toml not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ backend/pyproject.toml found${NC}"

# Check poetry.lock
if [ ! -f "backend/poetry.lock" ]; then
    echo -e "${YELLOW}⚠️ backend/poetry.lock not found - will be generated during build${NC}"
else
    echo -e "${GREEN}✅ backend/poetry.lock found${NC}"
fi

# Check Dockerfile
if [ ! -f "backend/Dockerfile" ]; then
    echo -e "${RED}❌ backend/Dockerfile not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ backend/Dockerfile found${NC}"

# Try building with verbose output
echo -e "${BLUE}🔨 Attempting to build backend with verbose output...${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}"

# Build with no cache and verbose output
docker-compose build --no-cache --progress=plain backend

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend build successful!${NC}"
else
    echo -e "${RED}❌ Backend build failed${NC}"
    echo -e "${BLUE}🔍 Common solutions:${NC}"
    echo -e "  1. Check if all dependencies are compatible"
    echo -e "  2. Try updating poetry.lock: cd backend && poetry lock"
    echo -e "  3. Check for system dependency issues"
    echo -e "  4. Try building with different Python version"
    
    echo -e "${BLUE}🔍 Next steps:${NC}"
    echo -e "  1. Run: cd backend && poetry lock"
    echo -e "  2. Run: ./update-dependencies.sh lock"
    echo -e "  3. Try building again: docker-compose build backend"
fi
