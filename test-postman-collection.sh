#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Postman Collection Functionality${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Test the exact same logic as the Postman collection
echo -e "${YELLOW}🔍 Testing Postman Collection Logic:${NC}"

# Simulate the Postman collection's user configuration
USERS=(
    "user:user:password:User (Read-only)"
    "testuser:testuser:password:User (Read-only)"
    "manager:manager:password:Manager (Read/Write)"
    "adminuser:adminuser:password:Admin (Full Access)"
)

# Test each user as if it were selected in Postman
for user_entry in "${USERS[@]}"; do
    user_key=$(echo "$user_entry" | cut -d: -f1)
    username=$(echo "$user_entry" | cut -d: -f2)
    password=$(echo "$user_entry" | cut -d: -f3)
    role=$(echo "$user_entry" | cut -d: -f4)
    
    echo -e "\n${BLUE}👤 Testing user: $user_key ($role)${NC}"
    
    # Simulate the Postman collection's token generation
    echo -e "${YELLOW}🔄 Getting fresh bearer token for $user_key...${NC}"
    
    TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$username&password=$password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret")
    
    TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
    EXPIRES_IN=$(echo $TOKEN_RESPONSE | jq -r '.expires_in')
    
    if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
        echo -e "${GREEN}✅ Bearer token generated successfully for $user_key${NC}"
        echo -e "${GREEN}⏰ Token expires in: $EXPIRES_IN seconds${NC}"
        echo -e "${GREEN}🔑 Token: ${TOKEN:0:50}...${NC}"
        
        # Test the token with API (simulate Postman request)
        echo -e "${YELLOW}🧪 Testing API call with token...${NC}"
        
        API_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/products/)
        API_SUCCESS=$(echo $API_RESPONSE | jq -r '.success // "unknown"')
        
        if [ "$API_SUCCESS" = "true" ]; then
            echo -e "${GREEN}✅ API call successful for $user_key${NC}"
        else
            echo -e "${RED}❌ API call failed for $user_key${NC}"
            echo -e "${RED}Response: $API_RESPONSE${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to get token for $user_key${NC}"
        echo -e "${RED}Response: $TOKEN_RESPONSE${NC}"
    fi
done

echo -e "\n${BLUE}📋 Postman Collection Troubleshooting:${NC}"
echo -e "${GREEN}1. Make sure you've imported EShop_Postman_Collection.json${NC}"
echo -e "${GREEN}2. Run a 'Switch to...' request first to set the current_user${NC}"
echo -e "${GREEN}3. Check the Postman console for token generation logs${NC}"
echo -e "${GREEN}4. Verify the Authorization header is being sent${NC}"
echo -e ""
echo -e "${BLUE}🔧 Common Issues:${NC}"
echo -e "${YELLOW}• 401 Unauthorized: Token not generated or expired${NC}"
echo -e "${YELLOW}• 422 Unprocessable Entity: Missing required fields (like picture_url)${NC}"
echo -e "${YELLOW}• 403 Forbidden: User doesn't have required permissions${NC}"
echo -e ""
echo -e "${BLUE}💡 Pro Tip:${NC}"
echo -e "${GREEN}Check the Postman console (View → Show Postman Console) to see the token generation logs!${NC}"
