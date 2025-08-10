@echo off
REM ==============================================================================
REM Keycloak Setup Script for Windows - eShop RBAC Configuration
REM ==============================================================================
setlocal enabledelayedexpansion

echo.
echo ===================================================================
echo             🔐 Setting up Keycloak for eShop with RBAC
echo ===================================================================
echo.

REM Check if curl is available
curl --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: curl is not installed or not in PATH
    echo Please install curl from https://curl.se/windows/
    pause
    exit /b 1
)

REM Check if jq is available (optional but recommended)
jq --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Warning: jq is not installed. JSON parsing will be limited.
    echo You can install jq from https://stedolan.github.io/jq/download/
    set JQ_AVAILABLE=false
) else (
    set JQ_AVAILABLE=true
)

REM Wait for Keycloak to be ready
echo ⏳ Waiting for Keycloak to be ready...
timeout /t 20 /nobreak >nul

REM Check if Keycloak is accessible
curl -s http://localhost:8080/ >nul 2>&1
if errorlevel 1 (
    echo ❌ Keycloak is not accessible at http://localhost:8080
    echo Please ensure Keycloak container is running:
    echo   docker ps ^| findstr keycloak
    echo   or
    echo   podman ps ^| findstr keycloak
    pause
    exit /b 1
)

echo ✅ Keycloak is accessible

REM Get admin token
echo 🔑 Getting admin token...
for /f "delims=" %%i in ('curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin&password=admin&grant_type=password&client_id=admin-cli"') do set TOKEN_RESPONSE=%%i

if "!JQ_AVAILABLE!"=="true" (
    for /f "delims=" %%i in ('echo !TOKEN_RESPONSE! ^| jq -r ".access_token"') do set ADMIN_TOKEN=%%i
) else (
    REM Simple fallback parsing without jq
    for /f "tokens=2 delims=:" %%a in ('echo !TOKEN_RESPONSE! ^| findstr "access_token"') do (
        set TEMP=%%a
        set TEMP=!TEMP:"=!
        set TEMP=!TEMP:,=!
        set ADMIN_TOKEN=!TEMP!
    )
)

if "!ADMIN_TOKEN!"=="null" (
    echo ❌ Failed to get admin token
    pause
    exit /b 1
)

if "!ADMIN_TOKEN!"=="" (
    echo ❌ Failed to get admin token
    pause
    exit /b 1
)

echo ✅ Admin token obtained

REM Create realm
echo 🏰 Creating 'eshop' realm...
curl -s -X POST http://localhost:8080/admin/realms -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "{\"realm\": \"eshop\", \"enabled\": true, \"displayName\": \"eShop Realm\"}" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Realm might already exist
) else (
    echo ✅ Realm 'eshop' created
)

REM Create client
echo 🔧 Creating 'eshop-api' client...
curl -s -X POST http://localhost:8080/admin/realms/eshop/clients -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "{\"clientId\": \"eshop-api\", \"enabled\": true, \"publicClient\": false, \"clientAuthenticatorType\": \"client-secret\", \"secret\": \"your-client-secret\", \"redirectUris\": [\"http://localhost:8000/*\"], \"webOrigins\": [\"http://localhost:8000\"], \"serviceAccountsEnabled\": true, \"authorizationServicesEnabled\": true, \"directAccessGrantsEnabled\": true, \"standardFlowEnabled\": true}" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Client might already exist
) else (
    echo ✅ Client 'eshop-api' created
)

REM Create roles
echo 👥 Creating RBAC roles...
curl -s -X POST http://localhost:8080/admin/realms/eshop/roles -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "{\"name\": \"user\", \"description\": \"Basic user role - can read data\"}" >nul 2>&1
echo ✅ Role 'user' created

curl -s -X POST http://localhost:8080/admin/realms/eshop/roles -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "{\"name\": \"manager\", \"description\": \"Manager role - can read and write data\"}" >nul 2>&1
echo ✅ Role 'manager' created

curl -s -X POST http://localhost:8080/admin/realms/eshop/roles -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "{\"name\": \"admin\", \"description\": \"Admin role - full access to all operations\"}" >nul 2>&1
echo ✅ Role 'admin' created

REM Create test users with different roles
echo 👤 Creating test users with RBAC roles...

REM Create admin user
echo Creating user: admin with role: admin
curl -s -X POST http://localhost:8080/admin/realms/eshop/users -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "{\"username\": \"admin\", \"email\": \"admin@example.com\", \"enabled\": true, \"emailVerified\": true, \"firstName\": \"Admin\", \"lastName\": \"User\", \"credentials\": [{\"type\": \"password\", \"value\": \"password\", \"temporary\": false}]}" >nul 2>&1

REM Get admin user ID and assign role
for /f "delims=" %%i in ('curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=admin" -H "Authorization: Bearer !ADMIN_TOKEN!"') do set USER_RESPONSE=%%i
if "!JQ_AVAILABLE!"=="true" (
    for /f "delims=" %%i in ('echo !USER_RESPONSE! ^| jq -r ".[0].id"') do set ADMIN_USER_ID=%%i
)

if "!JQ_AVAILABLE!"=="true" (
    for /f "delims=" %%i in ('curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/admin" -H "Authorization: Bearer !ADMIN_TOKEN!" ^| jq -r ".id"') do set ADMIN_ROLE_ID=%%i
    curl -s -X POST "http://localhost:8080/admin/realms/eshop/users/!ADMIN_USER_ID!/role-mappings/realm" -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "[{\"id\":\"!ADMIN_ROLE_ID!\",\"name\":\"admin\"}]" >nul 2>&1
)
echo ✅ Admin user created and configured

REM Create manager user
echo Creating user: manager with role: manager
curl -s -X POST http://localhost:8080/admin/realms/eshop/users -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "{\"username\": \"manager\", \"email\": \"manager@example.com\", \"enabled\": true, \"emailVerified\": true, \"firstName\": \"Manager\", \"lastName\": \"User\", \"credentials\": [{\"type\": \"password\", \"value\": \"password\", \"temporary\": false}]}" >nul 2>&1

REM Get manager user ID and assign role
for /f "delims=" %%i in ('curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=manager" -H "Authorization: Bearer !ADMIN_TOKEN!"') do set USER_RESPONSE=%%i
if "!JQ_AVAILABLE!"=="true" (
    for /f "delims=" %%i in ('echo !USER_RESPONSE! ^| jq -r ".[0].id"') do set MANAGER_USER_ID=%%i
    for /f "delims=" %%i in ('curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/manager" -H "Authorization: Bearer !ADMIN_TOKEN!" ^| jq -r ".id"') do set MANAGER_ROLE_ID=%%i
    curl -s -X POST "http://localhost:8080/admin/realms/eshop/users/!MANAGER_USER_ID!/role-mappings/realm" -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "[{\"id\":\"!MANAGER_ROLE_ID!\",\"name\":\"manager\"}]" >nul 2>&1
)
echo ✅ Manager user created and configured

REM Create regular user
echo Creating user: user with role: user
curl -s -X POST http://localhost:8080/admin/realms/eshop/users -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "{\"username\": \"user\", \"email\": \"user@example.com\", \"enabled\": true, \"emailVerified\": true, \"firstName\": \"Regular\", \"lastName\": \"User\", \"credentials\": [{\"type\": \"password\", \"value\": \"password\", \"temporary\": false}]}" >nul 2>&1

REM Get user ID and assign role
for /f "delims=" %%i in ('curl -s -X GET "http://localhost:8080/admin/realms/eshop/users?username=user" -H "Authorization: Bearer !ADMIN_TOKEN!"') do set USER_RESPONSE=%%i
if "!JQ_AVAILABLE!"=="true" (
    for /f "delims=" %%i in ('echo !USER_RESPONSE! ^| jq -r ".[0].id"') do set REGULAR_USER_ID=%%i
    for /f "delims=" %%i in ('curl -s -X GET "http://localhost:8080/admin/realms/eshop/roles/user" -H "Authorization: Bearer !ADMIN_TOKEN!" ^| jq -r ".id"') do set USER_ROLE_ID=%%i
    curl -s -X POST "http://localhost:8080/admin/realms/eshop/users/!REGULAR_USER_ID!/role-mappings/realm" -H "Authorization: Bearer !ADMIN_TOKEN!" -H "Content-Type: application/json" -d "[{\"id\":\"!USER_ROLE_ID!\",\"name\":\"user\"}]" >nul 2>&1
)
echo ✅ Regular user created and configured

REM Note: Minimal user set complete - no additional users needed

echo.
echo 🎉 Keycloak RBAC setup complete!
echo.
echo 📋 Access Points:
echo   • Keycloak Admin: http://localhost:8080/admin/ (admin/admin)
echo   • Realm: eshop
echo   • Client: eshop-api
echo.
echo 👥 Test Users ^& Roles:
echo   • admin/password (Admin role - full access)
echo   • manager/password (Manager role - read/write access)
echo   • user/password (User role - read-only access)
echo.
echo 🔐 RBAC Permissions:
echo   • Command endpoints (POST/PUT/DELETE): admin, manager
echo   • Query endpoints (GET): admin, manager, user
echo.
echo 🧪 Test Authentication:
echo   # Test user login (read-only)
echo   curl -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token ^
echo     -d "username=user&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret"
echo.
echo   # Test admin login (full access)
echo   curl -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token ^
echo     -d "username=admin&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret"
echo.
echo 🔧 Next Steps:
echo   1. Update your .env file with the correct client secret
echo   2. Test authentication with different user roles
echo   3. Verify RBAC is working on command vs query endpoints
echo.
pause
