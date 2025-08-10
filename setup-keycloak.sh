#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Setting up Keycloak for eShop with RBAC...${NC}"

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

# Create roles with proper hierarchy
echo -e "${BLUE}👥 Creating RBAC roles...${NC}"
ROLES=(
    '{"name": "user", "description": "Basic user role - can read data"}'
    '{"name": "manager", "description": "Manager role - can read and write data"}'
    '{"name": "admin", "description": "Admin role - full access to all operations"}'
)

for role_json in "${ROLES[@]}"; do
    ROLE_RESPONSE=$(curl -s -X POST http://localhost:8080/admin/realms/eshop/roles \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$role_json")
    
    if [ $? -eq 0 ]; then
        role_name=$(echo "$role_json" | jq -r '.name')
        echo -e "${GREEN}✅ Role '$role_name' created${NC}"
    else
        role_name=$(echo "$role_json" | jq -r '.name')
        echo -e "${YELLOW}⚠️ Role '$role_name' might already exist${NC}"
    fi
done

# Create test users with different roles
echo -e "${BLUE}👤 Creating test users with RBAC roles...${NC}"

# Test users with their roles
declare -A USERS=(
    ["admin"]="admin"
    ["manager"]="manager"
    ["user"]="user"
    ["testuser"]="user"  # Keep existing testuser for backward compatibility
)

for username in "${!USERS[@]}"; do
    role="${USERS[$username]}"
    
    # Create user
    USER_RESPONSE=$(curl -s -X POST http://localhost:8080/admin/realms/eshop/users \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"$username\",
            \"email\": \"$username@example.com\",
            \"enabled\": true,
            \"emailVerified\": true,
            \"firstName\": \"$(echo $username | sed 's/./\U&/') Test\",
            \"lastName\": \"User\",
            \"credentials\": [{
                \"type\": \"password\",
                \"value\": \"password\",
                \"temporary\": false
            }]
        }")

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ User '$username' created${NC}"
        
        # Get user ID and assign role
        USER_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=$username" \
            -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')
        
        if [ "$USER_ID" != "null" ] && [ -n "$USER_ID" ]; then
            # Get role ID
            ROLE_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/$role" \
                -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')
            
            if [ "$ROLE_ID" != "null" ] && [ -n "$ROLE_ID" ]; then
                # Assign role to user
                curl -s -X POST "http://localhost:8080/admin/realms/eshop/users/$USER_ID/role-mappings/realm" \
                    -H "Authorization: Bearer $ADMIN_TOKEN" \
                    -H "Content-Type: application/json" \
                    -d "[{\"id\":\"$ROLE_ID\",\"name\":\"$role\"}]" > /dev/null
                
                echo -e "${GREEN}✅ Role '$role' assigned to $username${NC}"
            else
                echo -e "${RED}❌ Failed to get role ID for '$role'${NC}"
            fi
        else
            echo -e "${RED}❌ Failed to get user ID for '$username'${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ User '$username' might already exist${NC}"
    fi
done

# Create composite roles for role hierarchy (optional)
echo -e "${BLUE}🔗 Setting up role hierarchy...${NC}"

# Get role IDs for composite role setup
ADMIN_ROLE_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/admin" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')

MANAGER_ROLE_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/manager" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')

USER_ROLE_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/user" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')

# Make admin role composite with manager and user roles
if [ "$ADMIN_ROLE_ID" != "null" ] && [ "$MANAGER_ROLE_ID" != "null" ] && [ "$USER_ROLE_ID" != "null" ]; then
    curl -s -X POST "http://localhost:8080/admin/realms/eshop/roles/admin/composites" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "[{\"id\":\"$MANAGER_ROLE_ID\",\"name\":\"manager\"}, {\"id\":\"$USER_ROLE_ID\",\"name\":\"user\"}]" > /dev/null
    
    echo -e "${GREEN}✅ Admin role configured as composite (includes manager and user)${NC}"
fi

# Make manager role composite with user role
if [ "$MANAGER_ROLE_ID" != "null" ] && [ "$USER_ROLE_ID" != "null" ]; then
    curl -s -X POST "http://localhost:8080/admin/realms/eshop/roles/manager/composites" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "[{\"id\":\"$USER_ROLE_ID\",\"name\":\"user\"}]" > /dev/null
    
    echo -e "${GREEN}✅ Manager role configured as composite (includes user)${NC}"
fi

echo -e "${GREEN}🎉 Keycloak RBAC setup complete!${NC}"
echo -e "${BLUE}📋 Access Points:${NC}"
echo -e "  • Keycloak Admin: http://localhost:8080/admin/ (admin/admin)"
echo -e "  • Realm: eshop"
echo -e "  • Client: eshop-api"
echo -e ""
echo -e "${BLUE}👥 Test Users & Roles:${NC}"
echo -e "  • admin/password (Admin role - full access)"
echo -e "  • manager/password (Manager role - read/write access)"
echo -e "  • user/password (User role - read-only access)"
echo -e "  • testuser/password (User role - read-only access)"
echo -e ""
echo -e "${BLUE}🔐 RBAC Permissions:${NC}"
echo -e "  • Command endpoints (POST/PUT/DELETE): admin, manager"
echo -e "  • Query endpoints (GET): admin, manager, user"
echo -e ""
echo -e "${BLUE}🔧 Next Steps:${NC}"
echo -e "  1. Update your .env file with the correct client secret"
echo -e "  2. Test authentication with different user roles"
echo -e "  3. Verify RBAC is working on command vs query endpoints" 