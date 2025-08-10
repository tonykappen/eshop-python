# Authentication & RBAC Guide for eShop Python

This guide provides comprehensive instructions for setting up authentication, creating users, managing roles, generating tokens, and using them in API calls with the eShop Python application.

## Table of Contents

1. [Overview](#overview)
2. [Keycloak Setup](#keycloak-setup)
3. [User Management](#user-management)
4. [Role Management](#role-management)
5. [Token Creation](#token-creation)
6. [API Usage with Tokens](#api-usage-with-tokens)
7. [RBAC Testing](#rbac-testing)
8. [Troubleshooting](#troubleshooting)

## Overview

The eShop Python application uses Keycloak for authentication and authorization with JWT tokens. The system implements Role-Based Access Control (RBAC) with three main roles:

- **admin**: Full access to all operations
- **manager**: Access to most operations except critical admin functions
- **user**: Read access and basic operations

## Keycloak Setup

### 1. Start Keycloak Container

```bash
# Using Podman (preferred)
podman run -d --name keycloak-eshop -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest start-dev

# Or using Docker
docker run -d --name keycloak-eshop -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest start-dev
```

### 2. Run Setup Script

```bash
chmod +x setup-keycloak.sh
./setup-keycloak.sh
```

### 3. Verify Keycloak is Running

```bash
# Check if Keycloak is running
curl -s http://localhost:8080/ | head -5

# Check realm configuration
curl -s http://localhost:8080/realms/eshop | python -c "import sys, json; data=json.load(sys.stdin); print(f'Realm: {data.get(\"realm\")}')"
```

## User Management

### Creating Users

#### Method 1: Using Admin API (Recommended)

```bash
# Get admin token
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))")

# Create a new user
curl -X POST "http://localhost:8080/admin/realms/eshop/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "firstName": "New",
    "lastName": "User",
    "enabled": true,
    "emailVerified": true,
    "credentials": [{
      "type": "password",
      "value": "password123",
      "temporary": false
    }]
  }'
```

#### Method 2: Using Keycloak Admin Console

1. Open http://localhost:8080/admin
2. Login with admin/admin
3. Go to "Users" → "Add user"
4. Fill in the details and save
5. Go to "Credentials" tab and set password

### User Examples

Here are examples of users with different roles:

```bash
# Admin User
curl -X POST "http://localhost:8080/admin/realms/eshop/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_user",
    "email": "admin@eshop.com",
    "firstName": "Admin",
    "lastName": "User",
    "enabled": true,
    "emailVerified": true,
    "credentials": [{
      "type": "password",
      "value": "admin123",
      "temporary": false
    }]
  }'

# Manager User
curl -X POST "http://localhost:8080/admin/realms/eshop/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "manager_user",
    "email": "manager@eshop.com",
    "firstName": "Manager",
    "lastName": "User",
    "enabled": true,
    "emailVerified": true,
    "credentials": [{
      "type": "password",
      "value": "manager123",
      "temporary": false
    }]
  }'

# Regular User
curl -X POST "http://localhost:8080/admin/realms/eshop/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "regular_user",
    "email": "user@eshop.com",
    "firstName": "Regular",
    "lastName": "User",
    "enabled": true,
    "emailVerified": true,
    "credentials": [{
      "type": "password",
      "value": "user123",
      "temporary": false
    }]
  }'
```

## Role Management

### Default Roles in eShop

The system recognizes these roles for RBAC:

- **admin**: Full system access
- **manager**: Management operations
- **user**: Basic user operations

### Creating Custom Roles

```bash
# Create a custom role
curl -X POST "http://localhost:8080/admin/realms/eshop/roles" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_role",
    "description": "Custom role for specific permissions"
  }'
```

### Assigning Roles to Users

```bash
# Get user ID
USER_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=regular_user" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')")

# Get role representation
ROLE_REP=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/user" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

# Assign role to user
curl -X POST "http://localhost:8080/admin/realms/eshop/users/$USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[$ROLE_REP]"
```

### Role Assignment Examples

```bash
# Assign admin role
curl -X POST "http://localhost:8080/admin/realms/eshop/users/$ADMIN_USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"id":"admin-role-id","name":"admin","description":"Administrator role"}]'

# Assign manager role
curl -X POST "http://localhost:8080/admin/realms/eshop/users/$MANAGER_USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"id":"manager-role-id","name":"manager","description":"Manager role"}]'

# Assign user role
curl -X POST "http://localhost:8080/admin/realms/eshop/users/$USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"id":"user-role-id","name":"user","description":"User role"}]'
```

## Token Creation

### 1. Client Credentials Flow (Service-to-Service)

```bash
# Get service token
SERVICE_TOKEN=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=eshop-api" \
  -d "client_secret=your-client-secret" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))")

echo "Service Token: $SERVICE_TOKEN"
```

### 2. Password Flow (User Authentication)

```bash
# Get user token for admin
ADMIN_TOKEN_USER=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=eshop-api" \
  -d "client_secret=your-client-secret" \
  -d "username=admin_user" \
  -d "password=admin123" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))")

# Get user token for manager
MANAGER_TOKEN=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=eshop-api" \
  -d "client_secret=your-client-secret" \
  -d "username=manager_user" \
  -d "password=manager123" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))")

# Get user token for regular user
USER_TOKEN=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=eshop-api" \
  -d "client_secret=your-client-secret" \
  -d "username=regular_user" \
  -d "password=user123" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))")
```

### 3. Token Information

```bash
# Decode token to see contents (base64 decode the payload)
echo $USER_TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data, indent=2))"
```

## API Usage with Tokens

### Basic Authentication Test

```bash
# Test authentication without token (should get 401)
curl -s http://localhost:8000/api/v1/auth/me

# Test with valid token (should get user info)
curl -s http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer $USER_TOKEN"
```

### RBAC Test Endpoint

```bash
# Test RBAC endpoint (any authenticated user)
curl -s http://localhost:8000/api/v1/rbac-test -H "Authorization: Bearer $USER_TOKEN"
```

### Catalog API Examples

#### Read Operations (Query Access - admin, manager, user)

```bash
# Get products (requires user, manager, or admin role)
curl -s http://localhost:8000/api/v1/products/ -H "Authorization: Bearer $USER_TOKEN"

# Get specific product
curl -s http://localhost:8000/api/v1/products/00000000-0000-0000-0000-000000000001 -H "Authorization: Bearer $USER_TOKEN"

# Get products with pagination
curl -s "http://localhost:8000/api/v1/products/?page=1&page_size=5" -H "Authorization: Bearer $USER_TOKEN"

# Search products
curl -s "http://localhost:8000/api/v1/products/?search_term=laptop" -H "Authorization: Bearer $USER_TOKEN"
```

#### Write Operations (Command Access - admin, manager only)

```bash
# Create product (requires admin or manager role)
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer $ADMIN_TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Laptop",
    "description": "High-performance laptop",
    "price": 1299.99,
    "picture_url": "laptop.jpg"
  }'

# This should fail with 403 if user doesn't have command access
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Unauthorized Product",
    "description": "This should fail",
    "price": 99.99,
    "picture_url": "fail.jpg"
  }'
```

## RBAC Testing

### Complete RBAC Test Script

```bash
#!/bin/bash

echo "🔐 RBAC Testing Script"
echo "======================"

# Get tokens for different users
echo "📝 Getting tokens..."
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=eshop-api" \
  -d "client_secret=your-client-secret" \
  -d "username=testuser" \
  -d "password=password" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null)

echo "✅ Tokens obtained"

# Test 1: Authentication
echo ""
echo "🧪 Test 1: Authentication"
echo "No token (should get 401):"
curl -s http://localhost:8000/api/v1/auth/me | head -1

echo ""
echo "With token (should get 200):"
curl -s http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer $ADMIN_TOKEN" | head -1

# Test 2: Query Access
echo ""
echo "🧪 Test 2: Query Access (Read Operations)"
echo "RBAC test endpoint:"
curl -s http://localhost:8000/api/v1/rbac-test -H "Authorization: Bearer $ADMIN_TOKEN"

echo ""
echo "Products endpoint:"
curl -s http://localhost:8000/api/v1/products/ -H "Authorization: Bearer $ADMIN_TOKEN" | head -3

# Test 3: Role Information
echo ""
echo "🧪 Test 3: User Role Information"
curl -s http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer $ADMIN_TOKEN" | python -c "import sys, json; data=json.load(sys.stdin); print(f'User: {data.get(\"preferred_username\")}, Roles: {data.get(\"roles\")}')" 2>/dev/null || echo "Token might be expired"

echo ""
echo "✅ RBAC testing completed"
```

### Expected RBAC Behavior

| Endpoint | Method | Admin | Manager | User | Anonymous |
|----------|---------|-------|---------|------|-----------|
| `/api/v1/auth/me` | GET | ✅ | ✅ | ✅ | ❌ |
| `/api/v1/rbac-test` | GET | ✅ | ✅ | ✅ | ❌ |
| `/api/v1/products/` | GET | ✅ | ✅ | ✅ | ❌ |
| `/api/v1/products/{id}` | GET | ✅ | ✅ | ✅ | ❌ |
| `/api/v1/products/` | POST | ✅ | ✅ | ❌ | ❌ |

## Troubleshooting

### Common Issues

#### 1. "Account is not fully set up"

**Problem**: User exists but can't authenticate

**Solution**:
```bash
# Reset user password and profile
USER_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=problematic_user" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')")

# Set password
curl -s -X PUT "http://localhost:8080/admin/realms/eshop/users/$USER_ID/reset-password" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "password",
    "value": "newpassword",
    "temporary": false
  }'

# Update profile
curl -s -X PUT "http://localhost:8080/admin/realms/eshop/users/$USER_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "emailVerified": true,
    "requiredActions": []
  }'
```

#### 2. "Invalid token" / "Audience doesn't match"

**Problem**: JWT token validation failing

**Solution**: The application accepts both "account" and "eshop-api" audiences. Ensure your Keycloak client is configured correctly.

#### 3. "Query access requires one of: admin, manager, user"

**Problem**: User doesn't have required roles

**Solution**: Assign appropriate roles to the user using the role management commands above.

#### 4. Token Expiration

**Problem**: Tokens expire after a certain time

**Solution**: Get a fresh token:
```bash
# Get new token
NEW_TOKEN=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=eshop-api" \
  -d "client_secret=your-client-secret" \
  -d "username=your_username" \
  -d "password=your_password" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))")
```

### Validation Commands

```bash
# Check if everything is working
echo "=== Keycloak Status ==="
curl -s http://localhost:8080/realms/eshop | python -c "import sys, json; data=json.load(sys.stdin); print(f'Realm: {data.get(\"realm\")}')"

echo "=== FastAPI Health ==="
curl -s http://localhost:8000/health | python -m json.tool

echo "=== Authentication Test ==="
curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -d "grant_type=client_credentials&client_id=eshop-api&client_secret=your-client-secret" | head -1
```

## Summary

This guide covers the complete authentication workflow for the eShop Python application:

1. **Setup**: Start Keycloak and run setup scripts
2. **Users**: Create users via Admin API or web console
3. **Roles**: Assign appropriate roles (admin, manager, user)
4. **Tokens**: Generate JWT tokens using various flows
5. **API Usage**: Make authenticated requests to protected endpoints
6. **Testing**: Verify RBAC is working correctly

The system is now fully operational with proper authentication and role-based authorization! 🎉
