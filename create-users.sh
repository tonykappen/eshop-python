#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Creating Keycloak users for eShop with RBAC...${NC}"

# Check if Keycloak is accessible
echo -e "${BLUE}⏳ Checking Keycloak accessibility...${NC}"
if ! curl -s http://localhost:8080/realms/eshop > /dev/null; then
    echo -e "${RED}❌ Keycloak is not accessible. Please ensure Keycloak is running on http://localhost:8080${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Keycloak is accessible${NC}"

# Get admin token
echo -e "${BLUE}🔑 Getting admin token...${NC}"
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin" \
    -d "password=admin" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" | jq -r '.access_token')

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
    echo -e "${RED}❌ Failed to get admin token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Admin token obtained${NC}"

# Define users with their roles and details
USERS=("user" "manager" "adminuser" "testuser")
ROLES=("user" "manager" "admin" "user")
NAMES=("User Test" "Manager Test" "Admin Test" "Test User")
EMAILS=("user@example.com" "manager@example.com" "admin@example.com" "testuser@example.com")

# Create users
for i in "${!USERS[@]}"; do
    username="${USERS[$i]}"
    role="${ROLES[$i]}"
    first_name="${NAMES[$i]}"
    email="${EMAILS[$i]}"
    
    echo -e "${BLUE}👤 Processing user: $username with role: $role${NC}"
    
    # Check if user already exists
    EXISTING_USER=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=$username" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if [ "$(echo "$EXISTING_USER" | jq 'length')" -gt 0 ]; then
        echo -e "${YELLOW}⚠️ User '$username' already exists, skipping creation${NC}"
        USER_ID=$(echo "$EXISTING_USER" | jq -r '.[0].id')
    else
        # Create user
        echo -e "${BLUE}📝 Creating user: $username${NC}"
        USER_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST http://localhost:8080/admin/realms/eshop/users \
            -H "Authorization: Bearer $ADMIN_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"username\": \"$username\",
                \"email\": \"$email\",
                \"enabled\": true,
                \"emailVerified\": true,
                \"firstName\": \"$first_name\",
                \"lastName\": \"User\",
                \"credentials\": [{
                    \"type\": \"password\",
                    \"value\": \"password\",
                    \"temporary\": false
                }]
            }")

        HTTP_STATUS=$(echo $USER_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        
        if [ "$HTTP_STATUS" -eq 201 ]; then
            echo -e "${GREEN}✅ User '$username' created successfully${NC}"
        else
            echo -e "${RED}❌ Failed to create user '$username' (HTTP $HTTP_STATUS)${NC}"
            echo -e "${RED}Response: $USER_RESPONSE${NC}"
            continue
        fi
        
        # Wait a moment for user creation to complete
        sleep 2
        
        # Get user ID
        USER_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=$username" \
            -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')
    fi
    
    if [ "$USER_ID" != "null" ] && [ -n "$USER_ID" ]; then
        echo -e "${GREEN}✅ User ID found: $USER_ID${NC}"
        
        # Check if role exists
        ROLE_EXISTS=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/$role" \
            -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')
        
        if [ "$ROLE_EXISTS" != "null" ] && [ -n "$ROLE_EXISTS" ]; then
            echo -e "${GREEN}✅ Role '$role' exists${NC}"
            
            # Check if user already has this role
            USER_ROLES=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/users/$USER_ID/role-mappings/realm" \
                -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[] | select(.name == "'$role'") | .name')
            
            if [ "$USER_ROLES" = "$role" ]; then
                echo -e "${YELLOW}⚠️ User '$username' already has role '$role'${NC}"
            else
                # Assign role to user
                echo -e "${BLUE}🔗 Assigning role '$role' to $username${NC}"
                ROLE_ASSIGN_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "http://localhost:8080/admin/realms/eshop/users/$USER_ID/role-mappings/realm" \
                    -H "Authorization: Bearer $ADMIN_TOKEN" \
                    -H "Content-Type: application/json" \
                    -d "[{\"id\":\"$ROLE_EXISTS\",\"name\":\"$role\"}]")
                
                ROLE_HTTP_STATUS=$(echo $ROLE_ASSIGN_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
                
                if [ "$ROLE_HTTP_STATUS" -eq 204 ]; then
                    echo -e "${GREEN}✅ Role '$role' successfully assigned to $username${NC}"
                else
                    echo -e "${RED}❌ Failed to assign role '$role' to $username (HTTP $ROLE_HTTP_STATUS)${NC}"
                    echo -e "${RED}Response: $ROLE_ASSIGN_RESPONSE${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ Role '$role' does not exist${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to get user ID for '$username'${NC}"
    fi
    
    echo -e "${BLUE}────────────────────────────────────────${NC}"
done

# Verify user creation and role assignments
echo -e "${BLUE}🔍 Verifying user creation and role assignments...${NC}"

for i in "${!USERS[@]}"; do
    username="${USERS[$i]}"
    role="${ROLES[$i]}"
    
    USER_INFO=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=$username" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0]')
    
    if [ "$USER_INFO" != "null" ]; then
        USER_ID=$(echo "$USER_INFO" | jq -r '.id')
        USER_ROLES=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/users/$USER_ID/role-mappings/realm" \
            -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[] | .name' | tr '\n' ', ' | sed 's/,$//')
        
        if [ -n "$USER_ROLES" ]; then
            echo -e "${GREEN}✅ $username: $USER_ROLES${NC}"
        else
            echo -e "${RED}❌ $username: No roles assigned${NC}"
        fi
    else
        echo -e "${RED}❌ $username: User not found${NC}"
    fi
done

# Test authentication for each user
echo -e "${BLUE}🧪 Testing authentication for each user...${NC}"

for i in "${!USERS[@]}"; do
    username="${USERS[$i]}"
    echo -e "${BLUE}🔐 Testing authentication for $username...${NC}"
    
    AUTH_RESPONSE=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$username" \
        -d "password=password" \
        -d "grant_type=password" \
        -d "client_id=eshop-api" \
        -d "client_secret=your-client-secret")
    
    TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
    
    if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
        echo -e "${GREEN}✅ $username: Authentication successful${NC}"
        
        # Test API access if application is running
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            API_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/products/ | jq -r '.success // .detail')
            if [ "$API_RESPONSE" = "true" ]; then
                echo -e "${GREEN}✅ $username: API access successful${NC}"
            else
                echo -e "${YELLOW}⚠️ $username: API access issue - $API_RESPONSE${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️ $username: Application not running, skipping API test${NC}"
        fi
    else
        ERROR=$(echo "$AUTH_RESPONSE" | jq -r '.error_description // .error // "Unknown error"')
        echo -e "${RED}❌ $username: Authentication failed - $ERROR${NC}"
    fi
    
    echo -e "${BLUE}────────────────────────────────────────${NC}"
done

echo -e "${GREEN}🎉 User creation and verification complete!${NC}"

echo -e "${BLUE}📋 Summary:${NC}"
echo -e "  • Keycloak Admin: http://localhost:8080/admin/ (admin/admin)"
echo -e "  • Realm: eshop"
echo -e "  • Client: eshop-api"
echo -e "  • Client Secret: your-client-secret"

echo -e "${BLUE}👥 Created Users:${NC}"
for i in "${!USERS[@]}"; do
    username="${USERS[$i]}"
    role="${ROLES[$i]}"
    echo -e "  • $username/password ($role role)"
done

echo -e "${BLUE}🔐 RBAC Permissions:${NC}"
echo -e "  • Command endpoints (POST/PUT/DELETE): admin, manager"
echo -e "  • Query endpoints (GET): admin, manager, user"

echo -e "${BLUE}🧪 Test Commands:${NC}"
echo -e "  # Test user authentication"
echo -e "  curl -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \\"
echo -e "    -d 'username=user&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret'"
echo -e ""
echo -e "  # Test API access"
echo -e "  curl -H 'Authorization: Bearer <token>' http://localhost:8000/api/v1/products/"
echo -e ""
echo -e "  # Test health check"
echo -e "  curl http://localhost:8000/health/detailed"

echo -e "${GREEN}✅ Setup complete!${NC}"
