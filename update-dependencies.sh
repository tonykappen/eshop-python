#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Updating dependencies for eShop backend...${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ docker-compose.yml not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Function to update dependencies
update_deps() {
    local update_flag=$1
    local cache_bust=$(date +%s)
    
    echo -e "${BLUE}🔨 Building backend with updated dependencies...${NC}"
    
    if [ "$update_flag" = "true" ]; then
        echo -e "${YELLOW}⚠️ This will update all dependencies to their latest compatible versions${NC}"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}❌ Cancelled${NC}"
            exit 1
        fi
    fi
    
    # Build with updated dependencies
    docker-compose build --build-arg CACHEBUST=$cache_bust --build-arg UPDATE_DEPS=$update_flag backend
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backend built successfully with updated dependencies${NC}"
        
        # Restart the backend service
        echo -e "${BLUE}🔄 Restarting backend service...${NC}"
        docker-compose up -d backend
        
        echo -e "${GREEN}✅ Backend restarted with updated dependencies${NC}"
    else
        echo -e "${RED}❌ Failed to build backend with updated dependencies${NC}"
        exit 1
    fi
}

# Parse command line arguments
case "${1:-}" in
    "force")
        echo -e "${YELLOW}🔄 Force updating all dependencies...${NC}"
        update_deps "true"
        ;;
    "check")
        echo -e "${BLUE}🔍 Checking for dependency updates...${NC}"
        cd backend
        if poetry show --outdated; then
            echo -e "${YELLOW}⚠️ Some dependencies have updates available${NC}"
            echo -e "${BLUE}Run './update-dependencies.sh force' to update them${NC}"
        else
            echo -e "${GREEN}✅ All dependencies are up to date${NC}"
        fi
        cd ..
        ;;
    "lock")
        echo -e "${BLUE}🔒 Regenerating lock file...${NC}"
        cd backend
        poetry lock
        cd ..
        update_deps "false"
        ;;
    *)
        echo -e "${BLUE}📋 Usage:${NC}"
        echo -e "  ${GREEN}./update-dependencies.sh check${NC}   - Check for outdated dependencies"
        echo -e "  ${GREEN}./update-dependencies.sh lock${NC}    - Regenerate lock file and rebuild"
        echo -e "  ${GREEN}./update-dependencies.sh force${NC}   - Update all dependencies to latest versions"
        echo -e ""
        echo -e "${BLUE}Examples:${NC}"
        echo -e "  # Check what's outdated"
        echo -e "  ./update-dependencies.sh check"
        echo -e ""
        echo -e "  # Regenerate lock file (recommended)"
        echo -e "  ./update-dependencies.sh lock"
        echo -e ""
        echo -e "  # Force update all dependencies (use with caution)"
        echo -e "  ./update-dependencies.sh force"
        ;;
esac
