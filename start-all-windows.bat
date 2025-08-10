@echo off
setlocal EnableDelayedExpansion

echo 🚀 Starting eShop Full Stack Application...

REM Function to check if a port is in use
:check_port
netstat -an | findstr ":%1 " >nul 2>&1
exit /b

REM Function to wait for service to be ready
:wait_for_service
set "url=%1"
set "service_name=%2"
set "max_attempts=30"
set "attempt=0"

echo ⏳ Waiting for %service_name% to be ready...

:wait_loop
curl -s "%url%" >nul 2>&1
if !errorlevel! == 0 (
    echo ✅ %service_name% is ready!
    exit /b 0
)
set /a attempt+=1
if !attempt! geq !max_attempts! (
    echo ❌ %service_name% failed to start after 60 seconds
    exit /b 1
)
timeout /t 2 >nul
goto wait_loop

REM Step 1: Start infrastructure services
echo 📦 Step 1: Starting infrastructure services...
if exist "setup-docker-windows.bat" (
    call setup-docker-windows.bat
) else (
    echo ❌ setup-docker-windows.bat not found
    exit /b 1
)

REM Wait for Keycloak to be ready
call :wait_for_service "http://localhost:8080/realms/eshop" "Keycloak"

REM Step 2: Start Backend API
echo 🔧 Step 2: Starting Backend API...

REM Kill any existing backend processes
echo 🧹 Cleaning up existing backend processes...
call :check_port 8000
if !errorlevel! == 0 (
    echo Port 8000 is in use, stopping existing processes...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 >nul
)

REM Start backend
echo 🚀 Starting FastAPI backend...
cd backend
start "" cmd /c "poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1"
cd ..

REM Wait for backend to be ready
call :wait_for_service "http://localhost:8000/health" "Backend API"

REM Step 3: Start Frontend
echo 🌐 Step 3: Starting Frontend...

REM Clean up existing frontend containers
docker rm -f eshop-frontend >nul 2>&1

REM Build and start frontend
cd frontend
echo 🔨 Building frontend container...
docker build -t eshop-frontend .
if !errorlevel! neq 0 (
    echo ❌ Frontend build failed
    exit /b 1
)

echo 🚀 Starting frontend container...
docker run -d --name eshop-frontend -p 3000:80 eshop-frontend
if !errorlevel! neq 0 (
    echo ❌ Frontend failed to start
    exit /b 1
)
cd ..

REM Wait for frontend to be ready
call :wait_for_service "http://localhost:3000" "Frontend"

REM Step 4: Display status and URLs
echo.
echo 🎉 eShop Full Stack Application Started Successfully!
echo.

echo 📋 Service Status:
for %%s in (eshop-postgres eshop-redis eshop-rabbitmq eshop-keycloak) do (
    docker ps --filter name=%%s --format "{{.Status}}" 2>nul
    if !errorlevel! == 0 (
        echo   ✅ %%s: Running
    ) else (
        echo   ❌ %%s: Not running
    )
)
echo   ✅ Backend API: Running
echo   ✅ Frontend: Running

echo.
echo 🌐 Access URLs:
echo   • Frontend (Login): http://localhost:3000
echo   • Backend API: http://localhost:8000
echo   • API Documentation: http://localhost:8000/docs
echo   • Health Checks: http://localhost:8000/health/detailed
echo   • Keycloak Admin: http://localhost:8080/admin (admin/admin)
echo   • RabbitMQ Management: http://localhost:15672 (guest/guest)

echo.
echo 👥 Test Users:
echo   • Admin: admin/password (Full access)
echo   • Manager: manager/password (Edit access)
echo   • User: user/password (Read-only access)

echo.
echo 🔧 Useful Commands:
echo   • View backend logs: type backend.log
echo   • View frontend logs: docker logs eshop-frontend
echo   • Stop all services: stop-all-windows.bat
echo   • Check health: curl http://localhost:8000/health/detailed

echo.
echo 🎯 Ready to test! Open http://localhost:3000 in your browser

pause
