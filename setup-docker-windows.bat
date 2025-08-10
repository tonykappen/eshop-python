@echo off
REM ==============================================================================
REM Docker Services Setup Script for Windows - eShop Python FastAPI
REM ==============================================================================
setlocal enabledelayedexpansion

echo.
echo ===================================================================
echo            🐳 Setting up Docker Services for eShop (Windows)
echo ===================================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker is not installed or not running
    echo Please install Docker Desktop from https://docker.com/products/docker-desktop
    echo Make sure Docker Desktop is running before executing this script
    pause
    exit /b 1
)

for /f "tokens=3" %%i in ('docker --version 2^>^&1') do set DOCKER_VERSION=%%i
echo ✅ Docker !DOCKER_VERSION! detected

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    REM Try docker compose (newer syntax)
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Error: docker-compose is not available
        echo Please ensure Docker Desktop includes Docker Compose
        pause
        exit /b 1
    ) else (
        set COMPOSE_CMD=docker compose
        for /f "tokens=4" %%i in ('docker compose version 2^>^&1') do set COMPOSE_VERSION=%%i
        echo ✅ Docker Compose !COMPOSE_VERSION! detected (using 'docker compose')
    )
) else (
    set COMPOSE_CMD=docker-compose
    for /f "tokens=3" %%i in ('docker-compose --version 2^>^&1') do set COMPOSE_VERSION=%%i
    echo ✅ Docker Compose !COMPOSE_VERSION! detected (using 'docker-compose')
)

REM Check if docker-compose.yml exists
if not exist "docker-compose.yml" (
    echo ❌ Error: docker-compose.yml not found
    echo Please run this script from the eShop project root directory
    pause
    exit /b 1
)

echo ✅ Found docker-compose.yml

echo.
echo 🧹 Cleaning up existing containers...
echo Stopping and removing existing containers...

REM Stop and remove existing containers
!COMPOSE_CMD! down --remove-orphans
if errorlevel 1 (
    echo ⚠️  Warning: Some containers might not have been running
)

REM Remove volumes (optional - be careful!)
echo.
set /p REMOVE_VOLUMES="Do you want to remove existing volumes? (This will delete all data) [y/N]: "
if /i "!REMOVE_VOLUMES!"=="y" (
    echo Removing volumes...
    !COMPOSE_CMD! down -v
    echo ✅ Volumes removed
)

echo.
echo 🏗️  Building and starting services...

REM Build and start all services
echo Building containers (this may take a few minutes)...
!COMPOSE_CMD! build --no-cache
if errorlevel 1 (
    echo ❌ Failed to build containers
    echo Check the error messages above and ensure all required files are present
    pause
    exit /b 1
)

echo ✅ Containers built successfully

echo.
echo 🚀 Starting services...
!COMPOSE_CMD! up -d
if errorlevel 1 (
    echo ❌ Failed to start services
    echo Run '!COMPOSE_CMD! logs' to see detailed error messages
    pause
    exit /b 1
)

echo ✅ Services started successfully

echo.
echo ⏳ Waiting for services to be ready...
echo This may take 1-2 minutes for all services to fully initialize...

REM Wait for services to start
timeout /t 60 /nobreak >nul

echo.
echo 🔍 Checking service status...

REM Check service status
!COMPOSE_CMD! ps

echo.
echo 🏥 Health check for critical services...

REM Health check for PostgreSQL
echo Checking PostgreSQL...
timeout /t 5 /nobreak >nul
docker exec eshop-postgres pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PostgreSQL might still be starting up
) else (
    echo ✅ PostgreSQL is ready
)

REM Health check for Redis
echo Checking Redis...
docker exec eshop-redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Redis might still be starting up
) else (
    echo ✅ Redis is ready
)

REM Health check for RabbitMQ
echo Checking RabbitMQ...
curl -s http://localhost:15672/ >nul 2>&1
if errorlevel 1 (
    echo ⚠️  RabbitMQ management interface might still be starting up
) else (
    echo ✅ RabbitMQ management interface is ready
)

REM Health check for Keycloak
echo Checking Keycloak...
curl -s http://localhost:8080/ >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Keycloak might still be starting up
) else (
    echo ✅ Keycloak is ready
)

REM Health check for Backend API (if running)
echo Checking Backend API...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Backend API might still be starting up or not included in this setup
) else (
    echo ✅ Backend API is ready
)

REM Health check for Frontend (if running)
echo Checking Frontend...
curl -s http://localhost:3000/ >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Frontend might still be starting up or not included in this setup
) else (
    echo ✅ Frontend is ready
)

echo.
echo 🎉 Docker services setup complete!
echo.
echo 📋 Service Status:
!COMPOSE_CMD! ps

echo.
echo 🌐 Service URLs:
echo   • Backend API: http://localhost:8000
echo   • API Documentation: http://localhost:8000/docs
echo   • Frontend: http://localhost:3000
echo   • Keycloak Admin: http://localhost:8080/admin/ (admin/admin)
echo   • RabbitMQ Management: http://localhost:15672/ (guest/guest)
echo   • PostgreSQL: localhost:5432 (postgres/postgres)
echo   • Redis: localhost:6379
echo.
echo 📊 Container Logs:
echo   • View all logs: !COMPOSE_CMD! logs
echo   • Follow logs: !COMPOSE_CMD! logs -f
echo   • Service-specific logs: !COMPOSE_CMD! logs [service-name]
echo.
echo 🔧 Useful Commands:
echo   • Stop all services: !COMPOSE_CMD! down
echo   • Restart services: !COMPOSE_CMD! restart
echo   • View service status: !COMPOSE_CMD! ps
echo   • Update and restart: !COMPOSE_CMD! pull ^&^& !COMPOSE_CMD! up -d
echo   • Clean up everything: !COMPOSE_CMD! down -v --remove-orphans
echo.
echo 🚀 Next Steps:
echo   1. Wait for all services to fully initialize (1-2 minutes)
echo   2. Run Keycloak setup: setup-keycloak-windows.bat
echo   3. Test the application: http://localhost:8000/docs
echo.
echo ⚠️  Troubleshooting:
if exist "logs" (
    echo   • Application logs: Check the 'logs' directory
)
echo   • Service logs: !COMPOSE_CMD! logs [service-name]
echo   • Restart specific service: !COMPOSE_CMD! restart [service-name]
echo   • Check resource usage: docker stats
echo.
echo Happy developing! 🎯
pause
