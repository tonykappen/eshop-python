#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔨 Trying different build approaches...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    exit 1
fi

# Function to try build
try_build() {
    local dockerfile=$1
    local description=$2
    
    echo -e "${BLUE}🔨 Trying: $description${NC}"
    echo -e "${YELLOW}Using Dockerfile: $dockerfile${NC}"
    
    # Set environment variable for docker-compose
    export BACKEND_DOCKERFILE=$dockerfile
    
    # Try to build
    if docker-compose build --no-cache backend; then
        echo -e "${GREEN}✅ Success with $dockerfile!${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed with $dockerfile${NC}"
        return 1
    fi
}

# Clean up any existing containers
echo -e "${BLUE}🧹 Cleaning up existing containers...${NC}"
docker-compose down 2>/dev/null || true

# Try the main Dockerfile first
echo -e "${BLUE}🔄 Attempt 1: Main Dockerfile${NC}"
if try_build "Dockerfile" "Main Dockerfile with enhanced dependency management"; then
    echo -e "${GREEN}🎉 Build successful with main Dockerfile!${NC}"
    exit 0
fi

# Try the simplified Dockerfile
echo -e "${BLUE}🔄 Attempt 2: Simplified Dockerfile${NC}"
if try_build "Dockerfile.simple" "Simplified Dockerfile"; then
    echo -e "${GREEN}🎉 Build successful with simplified Dockerfile!${NC}"
    echo -e "${YELLOW}💡 Consider using the simplified approach for now${NC}"
    exit 0
fi

# If both failed, try updating dependencies
echo -e "${BLUE}🔄 Attempt 3: Updating dependencies first${NC}"
echo -e "${YELLOW}Updating poetry.lock...${NC}"

cd backend
if poetry lock; then
    echo -e "${GREEN}✅ poetry.lock updated${NC}"
    cd ..
    
    # Try main Dockerfile again
    if try_build "Dockerfile" "Main Dockerfile after dependency update"; then
        echo -e "${GREEN}🎉 Build successful after dependency update!${NC}"
        exit 0
    fi
else
    echo -e "${RED}❌ Failed to update poetry.lock${NC}"
    cd ..
fi

echo -e "${RED}❌ All build attempts failed${NC}"
echo -e "${BLUE}🔍 Troubleshooting steps:${NC}"
echo -e "  1. Check Docker logs: docker-compose logs"
echo -e "  2. Try manual build: docker build -f backend/Dockerfile.simple backend/"
echo -e "  3. Check dependency conflicts in pyproject.toml"
echo -e "  4. Consider using a different Python base image"
