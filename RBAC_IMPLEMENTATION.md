# Role-Based Access Control (RBAC) Implementation

This document describes the RBAC implementation for the eShop application, which restricts command endpoints to admin users while allowing non-admin users to access query endpoints.

## Overview

The RBAC system is built on top of Keycloak authentication and provides fine-grained access control based on user roles. The implementation follows the principle of least privilege, ensuring that users only have access to the operations they need.

## Architecture

### Role Hierarchy

```
admin (full access)
├── manager (read/write access)
    └── user (read-only access)
```

### Permission Matrix

| Role    | Commands (POST/PUT/DELETE) | Queries (GET) | Description                    |
|---------|---------------------------|---------------|--------------------------------|
| admin   | ✅ Yes                    | ✅ Yes        | Full access to all operations  |
| manager | ✅ Yes                    | ✅ Yes        | Read/write access              |
| user    | ❌ No                     | ✅ Yes        | Read-only access               |
| none    | ❌ No                     | ❌ No         | No access (unauthenticated)    |

## Implementation Details

### 1. RBAC Module (`eshop/core/auth/rbac.py`)

The RBAC module provides the core functionality for role-based access control:

#### Key Components

- **`RBACConfig`**: Configuration class for RBAC settings
- **`require_command_access()`**: Dependency for command endpoints (admin/manager)
- **`require_query_access()`**: Dependency for query endpoints (admin/manager/user)
- **`require_specific_role()`**: Dependency for specific role requirements
- **`require_any_role()`**: Dependency for any of multiple roles

#### Usage Examples

```python
from eshop.core.auth.rbac import require_command_access, require_query_access

# Command endpoint (admin/manager only)
@router.post("/products")
async def create_product(
    data: CreateProductRequest,
    _: Any = Depends(require_command_access()),
) -> ProductResponse:
    # Only admin and manager users can access this endpoint
    pass

# Query endpoint (admin/manager/user)
@router.get("/products")
async def get_products(
    _: Any = Depends(require_query_access()),
) -> ProductsResponse:
    # All authenticated users can access this endpoint
    pass
```

### 2. CQRS Endpoint Factory Updates

The `CQRSEndpointFactory` has been updated to support RBAC:

```python
# Create command endpoint with RBAC protection
endpoint = factory.create_command_endpoint(
    command_factory=CreateProductCommand,
    auth_dependency=require_command_access()
)

# Create query endpoint with RBAC protection
endpoint = factory.create_query_endpoint(
    query_factory=GetProductsQuery,
    auth_dependency=require_query_access()
)
```

### 3. Catalog Endpoints Implementation

The catalog product endpoints demonstrate RBAC in action:

#### Query Endpoints (Read Access)
- `GET /api/v1/products/{id}` - Requires query access
- `GET /api/v1/products/` - Requires query access

#### Command Endpoints (Write Access)
- `POST /api/v1/products/` - Requires command access

## Setup Instructions

### 1. Start Keycloak

```bash
# Using Podman (recommended)
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

### 2. Run Keycloak Setup

```bash
chmod +x setup-keycloak.sh
./setup-keycloak.sh
```

This script will:
- Create the `eshop` realm
- Create the `eshop-api` client
- Create roles: `admin`, `manager`, `user`
- Create test users with appropriate roles
- Set up role hierarchy (admin includes manager, manager includes user)

### 3. Test Users

After setup, the following test users are available:

| Username | Password | Role    | Permissions                    |
|----------|----------|---------|--------------------------------|
| admin    | password | admin   | Full access (commands + queries) |
| manager  | password | manager | Read/write access              |
| user     | password | user    | Read-only access               |
| testuser | password | user    | Read-only access               |

## Testing RBAC

### 1. Automated Testing

Run the RBAC test script:

```bash
chmod +x test-rbac.sh
./test-rbac.sh
```

This script will:
- Test all user roles against command and query endpoints
- Verify that permissions are correctly enforced
- Test unauthenticated and invalid token scenarios
- Provide a comprehensive test report

### 2. Manual Testing

#### Test Command Access (Admin/Manager Only)

```bash
# Get admin token
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=password" \
  -d "grant_type=password" \
  -d "client_id=eshop-api" \
  -d "client_secret=your-client-secret" | jq -r '.access_token')

# Test command endpoint (should work for admin)
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Product","description":"Test","price":10.99,"picture_url":"http://example.com/image.jpg"}'

# Get user token
USER_TOKEN=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user" \
  -d "password=password" \
  -d "grant_type=password" \
  -d "client_id=eshop-api" \
  -d "client_secret=your-client-secret" | jq -r '.access_token')

# Test command endpoint (should fail for user)
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Product","description":"Test","price":10.99,"picture_url":"http://example.com/image.jpg"}'
```

#### Test Query Access (All Authenticated Users)

```bash
# Test query endpoint (should work for all authenticated users)
curl -X GET http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer $USER_TOKEN"

# Test unauthenticated access (should fail)
curl -X GET http://localhost:8000/api/v1/products/
```

## Configuration

### RBAC Configuration

You can customize the RBAC configuration by modifying the `RBACConfig` class:

```python
from eshop.core.auth.rbac import RBACConfig, require_command_access

# Custom RBAC configuration
custom_rbac_config = RBACConfig(
    command_roles=["admin", "manager", "supervisor"],
    query_roles=["admin", "manager", "supervisor", "user", "guest"],
    default_role=None
)

# Use custom configuration
@router.post("/products")
async def create_product(
    _: Any = Depends(require_command_access(custom_rbac_config)),
) -> ProductResponse:
    pass
```

### Environment Variables

Ensure your `.env` file contains the correct Keycloak configuration:

```env
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_CLIENT_ID=eshop-api
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_REALM=eshop
KEYCLOAK_CALLBACK_URI=http://localhost:8000/callback
```

## Security Considerations

### 1. Token Validation

- All tokens are validated with Keycloak on each request
- Expired tokens are automatically rejected
- Invalid tokens return 401 Unauthorized

### 2. Role Verification

- User roles are extracted from JWT tokens
- Role verification happens at the FastAPI dependency level
- Failed role checks return 403 Forbidden

### 3. Logging

- All RBAC decisions are logged for audit purposes
- Failed access attempts are logged with user context
- Successful access is logged at debug level

### 4. Error Handling

- Authentication failures return 401 Unauthorized
- Authorization failures return 403 Forbidden
- Clear error messages help with debugging

## Extending RBAC

### Adding New Roles

1. Add the role to Keycloak using the admin interface or API
2. Update the `RBACConfig` class to include the new role
3. Update the setup script to create the role automatically

### Adding New Permissions

1. Create new RBAC dependency functions in `eshop/core/auth/rbac.py`
2. Apply the dependencies to your endpoints
3. Update tests to verify the new permissions

### Custom Role Logic

For complex authorization logic, you can create custom dependencies:

```python
def require_product_owner() -> Callable[[KeycloakUser], KeycloakUser]:
    """Require user to be the owner of the product."""
    
    async def product_owner_checker(
        current_user: KeycloakUser = Depends(get_current_user),
        product_id: UUID = Path(...),
    ) -> KeycloakUser:
        # Custom logic to check if user owns the product
        # or has admin/manager role
        if "admin" in current_user.roles or "manager" in current_user.roles:
            return current_user
            
        # Check product ownership logic here
        # ...
        
        return current_user
    
    return product_owner_checker
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check token validity and Keycloak connectivity
2. **403 Forbidden**: Verify user has the required role
3. **Keycloak connection issues**: Ensure Keycloak is running and accessible

### Debug Mode

Enable debug logging to see detailed RBAC decisions:

```python
import logging
logging.getLogger("eshop.core.auth.rbac").setLevel(logging.DEBUG)
```

### Health Checks

Check Keycloak health:

```bash
curl http://localhost:8000/health/keycloak
```

## Best Practices

1. **Principle of Least Privilege**: Grant users only the permissions they need
2. **Role Hierarchy**: Use composite roles to simplify permission management
3. **Regular Audits**: Review user roles and permissions regularly
4. **Testing**: Always test RBAC with different user roles
5. **Documentation**: Document role requirements for each endpoint

## Future Enhancements

1. **Dynamic Permissions**: Support for dynamic permission checking based on data
2. **Permission Caching**: Cache role information to improve performance
3. **Audit Trail**: Enhanced logging and audit trail for security compliance
4. **Role Management API**: REST API for managing roles and permissions
5. **Multi-tenancy**: Support for multi-tenant role management
