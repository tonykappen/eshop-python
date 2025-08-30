# 🚀 Complete eShop API Collection Guide

## 📋 **Collection Overview**

The **eShop API Collection (Complete)** includes all available endpoints from the eShop application with automatic authentication and user selection.

### **🔑 Key Features:**
- ✅ **Automatic Token Generation** - No manual token management needed
- ✅ **User Selection** - Switch between different user roles easily
- ✅ **RBAC Testing** - Test role-based access control
- ✅ **Complete API Coverage** - All endpoints included
- ✅ **Health Monitoring** - Comprehensive health checks
- ✅ **Documentation Access** - OpenAPI and Swagger UI

## 📁 **Collection Structure**

### **1. User Selection**
Switch between different user roles to test RBAC:

- **Switch to User (Read-only)** - Basic user with read access
- **Switch to TestUser (Read-only)** - Alternative test user
- **Switch to Manager (Read/Write)** - Manager with create/update access
- **Switch to AdminUser (Full Access)** - Admin with full permissions

### **2. Health Checks**
Monitor application and service health:

- **Root Endpoint** - `GET /` - Application status
- **Basic Health Check** - `GET /health` - Simple health status
- **API Health Check** - `GET /api/v1/health` - API version info
- **Detailed Health Check** - `GET /health/detailed` - All services status
- **Database Health Check** - `GET /health/database` - PostgreSQL status
- **Redis Health Check** - `GET /health/redis` - Cache status
- **RabbitMQ Health Check** - `GET /health/rabbitmq` - Message broker status
- **Keycloak Health Check** - `GET /health/keycloak` - Authentication status

### **3. Authentication**
Test authentication and user management:

- **Get Current User Info** - `GET /api/v1/auth/me` - Current user details
- **Get Realm Info** - `GET /api/v1/auth-proxy/realm-info` - Keycloak realm info
- **Get Token via Proxy** - `POST /api/v1/auth-proxy/token` - Alternative token endpoint

### **4. Catalog Module**
Product management and catalog operations:

- **Test Catalog Router** - `GET /api/v1/test` - Catalog module test
- **Test RBAC** - `GET /api/v1/rbac-test` - RBAC functionality test
- **Get All Products** - `GET /api/v1/products/` - List all products
- **Get Products with Pagination** - `GET /api/v1/products/?page=1&page_size=5` - Paginated results
- **Get Products with Search** - `GET /api/v1/products/?search_term=laptop` - Search functionality
- **Get Product by ID** - `GET /api/v1/products/{id}` - Get specific product
- **Create Product** - `POST /api/v1/products/` - Create new product
- **Create Product (Manager/Admin Only)** - `POST /api/v1/products/` - Premium product creation

### **5. Documentation**
Access API documentation:

- **OpenAPI JSON** - `GET /openapi.json` - API specification
- **Swagger UI** - `GET /docs` - Interactive API documentation

### **6. RBAC Testing**
Test role-based access control:

- **Test User Access (Read-only)** - Test read access for different users
- **Test Create Product (Manager/Admin Only)** - Test write access restrictions

## 🎯 **How to Use**

### **Step 1: Import Collection**
1. Open Postman
2. Click **Import**
3. Select `EShop_Postman_Collection_Simple.json`
4. Verify collection is loaded

### **Step 2: Open Console**
1. Go to **View → Show Postman Console**
2. This shows authentication logs and RBAC test results

### **Step 3: Switch User**
1. Run any **"Switch to..."** request from User Selection folder
2. Check console for confirmation message
3. Example: `"Switched to manager (Read/Write access)"`

### **Step 4: Test APIs**
1. Run any API request - authentication is automatic
2. Check console for token generation logs
3. Verify response status and data

## 🔐 **Authentication Flow**

### **Automatic Token Generation:**
1. **Pre-request Script** runs before each request
2. **Gets current user** from collection variables
3. **Fetches fresh token** from Keycloak
4. **Sets Bearer token** automatically
5. **Request executes** with proper authentication

### **Console Output Example:**
```
Using user: manager
Token generated for manager
```

## 🛡️ **RBAC (Role-Based Access Control)**

### **User Roles:**
- **User/TestUser** - Read-only access to products
- **Manager** - Read/Write access to products
- **AdminUser** - Full access to all operations

### **Testing RBAC:**
1. **Switch to User** → Test read access (should work)
2. **Switch to User** → Test create product (should fail with 403)
3. **Switch to Manager** → Test create product (should work)
4. **Switch to AdminUser** → Test all operations (should work)

### **RBAC Test Results:**
- ✅ **200 OK** - Access granted
- ❌ **401 Unauthorized** - No authentication
- 🚫 **403 Forbidden** - Insufficient permissions

## 📊 **API Endpoints Summary**

| Category | Endpoint | Method | Auth Required | RBAC |
|----------|----------|--------|---------------|------|
| **Health** | `/` | GET | ❌ | - |
| **Health** | `/health` | GET | ❌ | - |
| **Health** | `/api/v1/health` | GET | ❌ | - |
| **Health** | `/health/detailed` | GET | ❌ | - |
| **Health** | `/health/database` | GET | ❌ | - |
| **Health** | `/health/redis` | GET | ❌ | - |
| **Health** | `/health/rabbitmq` | GET | ❌ | - |
| **Health** | `/health/keycloak` | GET | ❌ | - |
| **Auth** | `/api/v1/auth/me` | GET | ✅ | - |
| **Auth** | `/api/v1/auth-proxy/realm-info` | GET | ❌ | - |
| **Auth** | `/api/v1/auth-proxy/token` | POST | ❌ | - |
| **Catalog** | `/api/v1/test` | GET | ❌ | - |
| **Catalog** | `/api/v1/rbac-test` | GET | ❌ | - |
| **Catalog** | `/api/v1/products/` | GET | ✅ | Query Access |
| **Catalog** | `/api/v1/products/` | POST | ✅ | Command Access |
| **Catalog** | `/api/v1/products/{id}` | GET | ✅ | Query Access |
| **Docs** | `/openapi.json` | GET | ❌ | - |
| **Docs** | `/docs` | GET | ❌ | - |

## 🧪 **Testing Scenarios**

### **Scenario 1: Basic User Testing**
```bash
1. Run "Switch to User (Read-only)"
2. Run "Get All Products" → Should return 200 OK
3. Run "Create Product" → Should return 403 Forbidden
```

### **Scenario 2: Manager Testing**
```bash
1. Run "Switch to Manager (Read/Write)"
2. Run "Get All Products" → Should return 200 OK
3. Run "Create Product" → Should return 201 Created
```

### **Scenario 3: Health Monitoring**
```bash
1. Run "Basic Health Check" → Should return 200 OK
2. Run "Detailed Health Check" → Should show all services
3. Run "Database Health Check" → Should show DB status
```

### **Scenario 4: Authentication Testing**
```bash
1. Run "Get Current User Info" → Should return user details
2. Run "Get Realm Info" → Should return Keycloak info
3. Run "Get Token via Proxy" → Alternative token method
```

## 🔧 **Troubleshooting**

### **Issue: 401 Unauthorized**
**Solution:**
1. Check console for token generation logs
2. Verify "Switch to..." request was run first
3. Check Authorization header in request details

### **Issue: 403 Forbidden**
**Solution:**
1. Switch to a user with higher permissions (Manager/Admin)
2. Check RBAC test results in console
3. Verify user has required role

### **Issue: No Console Logs**
**Solution:**
1. View → Show Postman Console
2. Clear console and try again
3. Check for JavaScript errors

### **Issue: Token Expired**
**Solution:**
- The collection automatically generates fresh tokens
- No manual intervention needed

## 🎉 **Success Indicators**

✅ **Console shows:** "Using user: [username]"  
✅ **Console shows:** "Token generated for [username]"  
✅ **Request shows:** Authorization: Bearer [token]  
✅ **Response:** 200 OK with data  
✅ **RBAC tests:** Appropriate access granted/denied  

## 📚 **Additional Resources**

- **OpenAPI Documentation:** `http://localhost:8000/docs`
- **API Specification:** `http://localhost:8000/openapi.json`
- **Health Dashboard:** `http://localhost:8000/health/detailed`
- **Keycloak Admin:** `http://localhost:8080`

---

**The complete collection provides full API coverage with automatic authentication and RBAC testing! 🚀**


