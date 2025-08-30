# 🚀 eShop Postman Collection - User Selection Guide

## 📋 Overview

The updated eShop Postman collection now supports **dynamic user selection**, allowing you to easily switch between different users with different RBAC roles when testing the API.

## 🔧 Available Users & Roles

| User | Role | Permissions | Description |
|------|------|-------------|-------------|
| `user` | User | Read-only | Can view products, basic user access |
| `testuser` | User | Read-only | Can view products, basic user access |
| `manager` | Manager | Read/Write | Can view and create products |
| `adminuser` | Admin | Full Access | Can perform all operations |

## 🎯 How to Use User Selection

### Method 1: Using User Selection Requests (Recommended)

1. **Import the Collection**
   ```
   File → Import → EShop_Postman_Collection.json
   ```

2. **Switch Users**
   - Go to the **"User Selection"** folder
   - Run any of these requests to switch users:
     - `Switch to User (Read-only)`
     - `Switch to TestUser (Read-only)`
     - `Switch to Manager (Read/Write)`
     - `Switch to AdminUser (Full Access)`

3. **Test API Endpoints**
   - After switching users, run any API request
   - The collection will automatically use the selected user's credentials
   - Check the console to see which user is being used

### Method 2: Manual Variable Change

1. **Open Collection Variables**
   - Right-click on the collection → "Edit"
   - Go to "Variables" tab

2. **Change Current User**
   - Find the `current_user` variable
   - Change its value to one of:
     - `user`
     - `testuser`
     - `manager`
     - `adminuser`

3. **Save and Test**
   - Save the collection
   - Run any API request

## 🔍 Testing RBAC Permissions

### Read-Only Users (`user`, `testuser`)
- ✅ **Can do**: GET `/api/v1/products/`
- ❌ **Cannot do**: POST `/api/v1/products/` (403 Forbidden)

### Manager Users (`manager`)
- ✅ **Can do**: GET `/api/v1/products/`
- ✅ **Can do**: POST `/api/v1/products/`

### Admin Users (`adminuser`)
- ✅ **Can do**: All operations
- ✅ **Can do**: GET `/api/v1/products/`
- ✅ **Can do**: POST `/api/v1/products/`

## 📊 Console Output

When you run requests, check the Postman console to see:

```
👤 Using user: adminuser (Admin (Full Access))
🔄 Getting fresh bearer token for adminuser...
✅ Bearer token generated successfully for adminuser
⏰ Token expires in: 300 seconds
🔑 Token: eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6RDdmNHp0TTVlUUllQkZZSUlyRzkydjB3OHFuRDZobTJsQ2tmOFZ0MWNRIn0...
```

## 🧪 RBAC Test Requests

The collection includes special test requests in the **"RBAC Tests"** folder:

### 1. Test Current User Access
- Tests GET `/api/v1/products/` with current user
- Shows access results in console

### 2. Test Create Product (Admin/Manager Only)
- Tests POST `/api/v1/products/` with current user
- Shows whether user has write permissions

## 🔄 Automatic Token Management

The collection automatically:
- ✅ Generates fresh tokens for each request
- ✅ Handles token expiration (401 responses)
- ✅ Refreshes tokens when needed
- ✅ Uses the correct user credentials

## 🎯 Quick Start Workflow

1. **Import Collection**
   ```
   Import EShop_Postman_Collection.json
   ```

2. **Switch to User**
   ```
   Run: "Switch to User (Read-only)"
   ```

3. **Test Read Access**
   ```
   Run: "Get All Products"
   ```

4. **Switch to Manager**
   ```
   Run: "Switch to Manager (Read/Write)"
   ```

5. **Test Write Access**
   ```
   Run: "Create Product"
   ```

6. **Switch to Admin**
   ```
   Run: "Switch to AdminUser (Full Access)"
   ```

7. **Test Full Access**
   ```
   Run: Any API request
   ```

## 🔧 Troubleshooting

### Issue: "Invalid user" error
**Solution**: Check that `current_user` variable is set to one of:
- `user`
- `testuser`
- `manager`
- `adminuser`

### Issue: 401 Unauthorized
**Solution**: The collection will automatically refresh the token. If it persists:
1. Check that Keycloak is running
2. Verify user credentials in the setup
3. Run a "Switch to..." request to reset

### Issue: 403 Forbidden
**Solution**: This is expected behavior for read-only users trying to perform write operations.

## 📝 Example Test Scenarios

### Scenario 1: Test User Permissions
```
1. Switch to User (Read-only)
2. Test Current User Access → Should succeed
3. Test Create Product → Should fail (403)
```

### Scenario 2: Test Manager Permissions
```
1. Switch to Manager (Read/Write)
2. Test Current User Access → Should succeed
3. Test Create Product → Should succeed
```

### Scenario 3: Test Admin Permissions
```
1. Switch to AdminUser (Full Access)
2. Test Current User Access → Should succeed
3. Test Create Product → Should succeed
```

## 🎉 Benefits

- **Easy User Switching**: No need to manually change credentials
- **Automatic Token Management**: Handles authentication automatically
- **RBAC Testing**: Easy to test different permission levels
- **Clear Console Output**: See exactly which user is being used
- **Consistent Testing**: Same requests work with different users

## 🔗 Related Files

- `EShop_Postman_Collection.json` - The updated collection
- `test-postman-users.sh` - Script to test all users
- `setup-keycloak.sh` - Script to set up users in Keycloak

---

**Happy Testing! 🚀**


