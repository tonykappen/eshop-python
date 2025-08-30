#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Postman Collection with Different Users${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════${NC}"

# Test all users
USERS=("user" "testuser" "manager" "adminuser")
ROLES=("User (Read-only)" "User (Read-only)" "Manager (Read/Write)" "Admin (Full Access)")

for i in "${!USERS[@]}"; do
    user="${USERS[$i]}"
    role="${ROLES[$i]}"
    
    echo -e "\n${YELLOW}🔍 Testing User: $user ($role)${NC}"
    
    # Get token
    TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$user&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret")
    
    TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
    
    if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
        echo -e "${GREEN}✅ Token obtained for $user${NC}"
        
        # Test GET products (should work for all users)
        GET_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/products/)
        GET_STATUS=$(echo $GET_RESPONSE | jq -r '.success // "unknown"')
        
        if [ "$GET_STATUS" = "true" ]; then
            echo -e "${GREEN}✅ GET /products - Success${NC}"
        else
            echo -e "${RED}❌ GET /products - Failed${NC}"
        fi
        
        # Test POST product (should only work for manager and admin)
        POST_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/products/ \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"name":"Test Product","description":"Test","price":99.99,"category":"Test","stock_quantity":10}')
        
        POST_STATUS=$(echo $POST_RESPONSE | jq -r '.success // "unknown"')
        
        if [ "$POST_STATUS" = "true" ]; then
            echo -e "${GREEN}✅ POST /products - Success (has write access)${NC}"
        elif echo "$POST_RESPONSE" | grep -q "403"; then
            echo -e "${YELLOW}🚫 POST /products - Forbidden (read-only user)${NC}"
        else
            echo -e "${RED}❌ POST /products - Failed${NC}"
        fi
        
    else
        echo -e "${RED}❌ Failed to get token for $user${NC}"
    fi
done

echo -e "\n${BLUE}📋 Postman Collection Usage Instructions:${NC}"
echo -e "${GREEN}1. Import EShop_Postman_Collection.json into Postman${NC}"
echo -e "${GREEN}2. Go to 'User Selection' folder${NC}"
echo -e "${GREEN}3. Run any 'Switch to...' request to change users${NC}"
echo -e "${GREEN}4. Then run any API request - it will use the selected user${NC}"
echo -e ""
echo -e "${BLUE}🔧 Available Users:${NC}"
echo -e "  • ${YELLOW}user${NC} - Read-only access"
echo -e "  • ${YELLOW}testuser${NC} - Read-only access"  
echo -e "  • ${YELLOW}manager${NC} - Read/Write access"
echo -e "  • ${YELLOW}adminuser${NC} - Full access"
echo -e ""
echo -e "${BLUE}💡 Pro Tip:${NC}"
echo -e "  Check the Postman console to see which user is being used for each request!"


