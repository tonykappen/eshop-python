@echo off
REM ==============================================================================
REM Complete eShop Setup Script for Windows - One-Click Installation
REM ==============================================================================
setlocal enabledelayedexpansion

echo.
echo ===================================================================
echo                🎯 eShop Complete Setup for Windows
echo ===================================================================
echo.
echo This script will set up the complete eShop development environment:
echo   1. Development environment (Python, Poetry, dependencies)
echo   2. Docker services (PostgreSQL, Redis, RabbitMQ, Keycloak)
echo   3. Authentication setup (Keycloak realm, users, roles)
echo.
echo Prerequisites:
echo   - Python 3.12+ installed
echo   - Docker Desktop installed and running
echo.
set /p CONTINUE="Do you want to continue with the complete setup? [Y/n]: "
if /i "!CONTINUE!"=="n" (
    echo Setup cancelled.
    pause
    exit /b 0
)

echo.
echo ===================================================================
echo                    Step 1: Development Environment
echo ===================================================================
echo.

call setup-dev-windows.bat
if errorlevel 1 (
    echo ❌ Development environment setup failed
    pause
    exit /b 1
)

echo.
echo ===================================================================
echo                    Step 2: Docker Services
echo ===================================================================
echo.

call setup-docker-windows.bat
if errorlevel 1 (
    echo ❌ Docker services setup failed
    pause
    exit /b 1
)

echo.
echo ===================================================================
echo                    Step 3: Authentication Setup
echo ===================================================================
echo.

echo Waiting for Keycloak to fully initialize...
timeout /t 60 /nobreak >nul

call setup-keycloak-windows.bat
if errorlevel 1 (
    echo ❌ Keycloak setup failed
    pause
    exit /b 1
)

echo.
echo ===================================================================
echo                    🎉 Setup Complete!
echo ===================================================================
echo.
echo ✅ Development environment configured
echo ✅ Docker services running
echo ✅ Authentication (Keycloak) configured
echo ✅ Database migrations applied
echo ✅ Test users created
echo.
echo 🌐 Your eShop application is ready!
echo.
echo 📋 Quick Access URLs:
echo   • Backend API: http://localhost:8000/docs
echo   • Frontend: http://localhost:3000
echo   • Keycloak Admin: http://localhost:8080/admin/ (admin/admin)
echo.
echo 👥 Test Users (Minimal Set):
echo   • admin/password (Full access)
echo   • manager/password (Read/Write access)
echo   • user/password (Read-only access)
echo.
echo 🚀 To start development:
echo   1. Open a new Command Prompt
echo   2. cd backend
echo   3. poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo 📖 For detailed instructions, see: README-WINDOWS.md
echo.
echo Happy coding! 🎯
pause
