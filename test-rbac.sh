#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing RBAC Implementation...${NC}"

# Check if FastAPI app is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}❌ FastAPI app is not running at http://localhost:8000${NC}"
    echo -e "${YELLOW}Please start the application first:${NC}"
    echo -e "  poetry run uvicorn eshop.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo -e "${GREEN}✅ FastAPI app is running${NC}"

# Function to get token for a user
get_token() {
    local username=$1
    local password=$2
    
    local token=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$username" \
        -d "password=$password" \
        -d "grant_type=password" \
        -d "client_id=eshop-api" \
        -d "client_secret=your-client-secret" | jq -r '.access_token')
    
    echo "$token"
}

# Function to test endpoint access
test_endpoint() {
    local method=$1
    local endpoint=$2
    local token=$3
    local expected_status=$4
    local test_name=$5
    
    local response
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json \
            -H "Authorization: Bearer $token" \
            "http://localhost:8000$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d '{"name":"Test Product","description":"Test Description","price":10.99,"picture_url":"http://example.com/image.jpg"}' \
            "http://localhost:8000$endpoint")
    fi
    
    local status_code=${response: -3}
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ $test_name: $method $endpoint - Status $status_code (Expected: $expected_status)${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name: $method $endpoint - Status $status_code (Expected: $expected_status)${NC}"
        if [ -f /tmp/response.json ]; then
            echo -e "${YELLOW}Response: $(cat /tmp/response.json)${NC}"
        fi
        return 1
    fi
}

# Test users and their expected permissions
declare -A USERS=(
    ["admin"]="password"
    ["manager"]="password"
    ["user"]="password"
)

echo -e "${BLUE}🔑 Getting tokens for test users...${NC}"

# Get tokens for all users
declare -A TOKENS
for username in "${!USERS[@]}"; do
    password="${USERS[$username]}"
    token=$(get_token "$username" "$password")
    
    if [ "$token" != "null" ] && [ -n "$token" ]; then
        TOKENS["$username"]="$token"
        echo -e "${GREEN}✅ Token obtained for $username${NC}"
    else
        echo -e "${RED}❌ Failed to get token for $username${NC}"
        exit 1
    fi
done

echo -e "${BLUE}🧪 Testing RBAC permissions...${NC}"

# Test results tracking
total_tests=0
passed_tests=0

# Test Query Endpoints (should work for all authenticated users)
echo -e "${BLUE}📖 Testing Query Endpoints (GET)...${NC}"

for username in "${!TOKENS[@]}"; do
    token="${TOKENS[$username]}"
    
    # Test GET /api/v1/products/ (query endpoint)
    if test_endpoint "GET" "/api/v1/products/" "$token" "200" "Query access for $username"; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Test GET /api/v1/products/{id} (query endpoint)
    if test_endpoint "GET" "/api/v1/products/00000000-0000-0000-0000-000000000001" "$token" "404" "Query access for $username (not found)"; then
        ((passed_tests++))
    fi
    ((total_tests++))
done

# Test Command Endpoints (should only work for admin and manager)
echo -e "${BLUE}✏️ Testing Command Endpoints (POST)...${NC}"

for username in "${!TOKENS[@]}"; do
    token="${TOKENS[$username]}"
    
    # Test POST /api/v1/products/ (command endpoint)
    if [ "$username" = "admin" ] || [ "$username" = "manager" ]; then
        # Admin and manager should have access (200 or 422 for validation errors)
        if test_endpoint "POST" "/api/v1/products/" "$token" "422" "Command access for $username (validation expected)"; then
            ((passed_tests++))
        fi
    else
        # User should be denied (403)
        if test_endpoint "POST" "/api/v1/products/" "$token" "403" "Command access denied for $username"; then
            ((passed_tests++))
        fi
    fi
    ((total_tests++))
done

# Test unauthenticated access
echo -e "${BLUE}🚫 Testing Unauthenticated Access...${NC}"

# Test query endpoint without token
if test_endpoint "GET" "/api/v1/products/" "" "401" "Unauthenticated query access"; then
    ((passed_tests++))
fi
((total_tests++))

# Test command endpoint without token
if test_endpoint "POST" "/api/v1/products/" "" "401" "Unauthenticated command access"; then
    ((passed_tests++))
fi
((total_tests++))

# Test invalid token
echo -e "${BLUE}🔒 Testing Invalid Token...${NC}"

if test_endpoint "GET" "/api/v1/products/" "invalid-token" "401" "Invalid token query access"; then
    ((passed_tests++))
fi
((total_tests++))

if test_endpoint "POST" "/api/v1/products/" "invalid-token" "401" "Invalid token command access"; then
    ((passed_tests++))
fi
((total_tests++))

# Summary
echo -e "${BLUE}📊 RBAC Test Summary${NC}"
echo -e "  Total Tests: $total_tests"
echo -e "  Passed: $passed_tests"
echo -e "  Failed: $((total_tests - passed_tests))"

if [ $passed_tests -eq $total_tests ]; then
    echo -e "${GREEN}🎉 All RBAC tests passed!${NC}"
    echo -e "${BLUE}✅ RBAC Implementation is working correctly${NC}"
    echo -e ""
    echo -e "${BLUE}📋 Permission Summary:${NC}"
    echo -e "  • Admin users: Can access both commands and queries"
    echo -e "  • Manager users: Can access both commands and queries"
    echo -e "  • User users: Can only access queries (read-only)"
    echo -e "  • Unauthenticated: No access to any endpoints"
    exit 0
else
    echo -e "${RED}❌ Some RBAC tests failed${NC}"
    echo -e "${YELLOW}Please check the implementation and Keycloak configuration${NC}"
    exit 1
fi
