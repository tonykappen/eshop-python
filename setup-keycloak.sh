#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Setting up Keycloak for eShop...${NC}"

# Wait for Keycloak to be ready
echo -e "${BLUE}⏳ Waiting for Keycloak to be ready...${NC}"
sleep 20

# Check if Keycloak is accessible
if ! curl -s http://localhost:8080/ > /dev/null; then
    echo -e "${RED}❌ Keycloak is not accessible at http://localhost:8080${NC}"
    echo -e "${YELLOW}Please ensure Keycloak container is running:${NC}"
    echo -e "  podman ps | grep keycloak"
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

if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}❌ Failed to get admin token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Admin token obtained${NC}"

# Create realm
echo -e "${BLUE}🏰 Creating 'eshop' realm...${NC}"
REALM_RESPONSE=$(curl -s -X POST http://localhost:8080/admin/realms \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "realm": "eshop",
        "enabled": true,
        "displayName": "eShop Realm"
    }')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Realm 'eshop' created${NC}"
else
    echo -e "${YELLOW}⚠️ Realm might already exist${NC}"
fi

# Create client
echo -e "${BLUE}🔧 Creating 'eshop-api' client...${NC}"
CLIENT_RESPONSE=$(curl -s -X POST http://localhost:8080/admin/realms/eshop/clients \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "clientId": "eshop-api",
        "enabled": true,
        "publicClient": false,
        "clientAuthenticatorType": "client-secret",
        "secret": "your-client-secret",
        "redirectUris": ["http://localhost:8000/*"],
        "webOrigins": ["http://localhost:8000"],
        "serviceAccountsEnabled": true,
        "authorizationServicesEnabled": true,
        "directAccessGrantsEnabled": true,
        "standardFlowEnabled": true
    }')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Client 'eshop-api' created${NC}"
else
    echo -e "${YELLOW}⚠️ Client might already exist${NC}"
fi

# Create roles
echo -e "${BLUE}👥 Creating roles...${NC}"
ROLES=("admin" "user" "manager")

for role in "${ROLES[@]}"; do
    ROLE_RESPONSE=$(curl -s -X POST http://localhost:8080/admin/realms/eshop/roles \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$role\",
            \"description\": \"$role role for eShop\"
        }")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Role '$role' created${NC}"
    else
        echo -e "${YELLOW}⚠️ Role '$role' might already exist${NC}"
    fi
done

# Create test user
echo -e "${BLUE}👤 Creating test user...${NC}"
USER_RESPONSE=$(curl -s -X POST http://localhost:8080/admin/realms/eshop/users \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "email": "test@example.com",
        "enabled": true,
        "emailVerified": true,
        "credentials": [{
            "type": "password",
            "value": "password",
            "temporary": false
        }]
    }')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test user 'testuser' created${NC}"
    
    # Get user ID and assign role
    USER_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=testuser" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')
    
    if [ "$USER_ID" != "null" ] && [ -n "$USER_ID" ]; then
        # Get role ID
        ROLE_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/user" \
            -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')
        
        if [ "$ROLE_ID" != "null" ] && [ -n "$ROLE_ID" ]; then
            # Assign role to user
            curl -s -X POST "http://localhost:8080/admin/realms/eshop/users/$USER_ID/role-mappings/realm" \
                -H "Authorization: Bearer $ADMIN_TOKEN" \
                -H "Content-Type: application/json" \
                -d "[{\"id\":\"$ROLE_ID\",\"name\":\"user\"}]" > /dev/null
            
            echo -e "${GREEN}✅ Role 'user' assigned to testuser${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️ Test user might already exist${NC}"
fi

echo -e "${GREEN}🎉 Keycloak setup complete!${NC}"
echo -e "${BLUE}📋 Access Points:${NC}"
echo -e "  • Keycloak Admin: http://localhost:8080/admin/ (admin/admin)"
echo -e "  • Realm: eshop"
echo -e "  • Client: eshop-api"
echo -e "  • Test User: testuser/password"
echo -e ""
echo -e "${BLUE}🔧 Next Steps:${NC}"
echo -e "  1. Update your .env file with the correct client secret"
echo -e "  2. Test authentication with the health check endpoint"
echo -e "  3. Use the test user credentials for API testing" 