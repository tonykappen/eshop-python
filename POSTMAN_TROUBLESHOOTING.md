# 🔧 Postman Collection Troubleshooting Guide

## 🚨 **Issue: 401 Unauthorized + SyntaxError**

### **Problem:**
- Getting 401 Unauthorized errors
- "SyntaxError: Unexpected token '{'" in Postman console
- No Authorization header being sent

### **Root Cause:**
The original Postman collection has JavaScript syntax issues that prevent the pre-request script from executing properly.

## ✅ **Solution: Use Simplified Collection**

### **Step 1: Import Simplified Collection**
1. **Delete** the old collection from Postman
2. **Import** `EShop_Postman_Collection_Simple.json`
3. **Verify** the collection is loaded correctly

### **Step 2: Test the Collection**
1. **Open Postman Console** (View → Show Postman Console)
2. **Run** "Switch to User" from User Selection folder
3. **Run** "Get All Products" from Products folder
4. **Check** console for logs

### **Expected Console Output:**
```
Using user: user
Token generated for user
```

## 🔍 **Alternative: Manual Testing**

If Postman continues to have issues, you can test manually:

### **Test with curl:**
```bash
# Get token for user
TOKEN=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret" | \
  jq -r '.access_token')

# Test API
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/products/
```

### **Test with our script:**
```bash
./test-postman-collection.sh
```

## 🎯 **Working Collection Features**

### **User Selection:**
- ✅ Switch to User (Read-only)
- ✅ Switch to Manager (Read/Write)  
- ✅ Switch to AdminUser (Full Access)

### **API Endpoints:**
- ✅ Get All Products (GET)
- ✅ Create Product (POST) - includes picture_url
- ✅ Health Check (GET)

### **Authentication:**
- ✅ Automatic token generation
- ✅ Bearer token authentication
- ✅ User-specific credentials

## 🔧 **Common Issues & Fixes**

### **Issue 1: "SyntaxError: Unexpected token '{'"**
**Fix:** Use the simplified collection (`EShop_Postman_Collection_Simple.json`)

### **Issue 2: 401 Unauthorized**
**Fix:** 
1. Check console for token generation logs
2. Verify "Switch to..." request was run first
3. Check Authorization header in request details

### **Issue 3: 422 Unprocessable Entity (Create Product)**
**Fix:** The simplified collection includes `picture_url` field in the Create Product request

### **Issue 4: No console logs**
**Fix:**
1. View → Show Postman Console
2. Clear console and try again
3. Check for JavaScript errors

## 📋 **Step-by-Step Testing**

### **1. Import Collection**
```
File → Import → EShop_Postman_Collection_Simple.json
```

### **2. Open Console**
```
View → Show Postman Console
```

### **3. Switch User**
```
Run: "Switch to User" (from User Selection folder)
Expected: "Switched to user" in console
```

### **4. Test API**
```
Run: "Get All Products" (from Products folder)
Expected: 200 OK with products data
```

### **5. Check Authorization**
```
In request details, verify Authorization header contains Bearer token
```

## 🎉 **Success Indicators**

✅ **Console shows:** "Using user: [username]"  
✅ **Console shows:** "Token generated for [username]"  
✅ **Request shows:** Authorization: Bearer [token]  
✅ **Response:** 200 OK with data  

## 🆘 **Still Having Issues?**

1. **Check Keycloak:** `curl http://localhost:8080/realms/eshop`
2. **Check API:** `curl http://localhost:8000/health`
3. **Test manually:** Use the curl commands above
4. **Use our script:** `./test-postman-collection.sh`

---

**The simplified collection should resolve the syntax errors and get authentication working! 🚀**


