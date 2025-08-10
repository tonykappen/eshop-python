@echo off
setlocal EnableDelayedExpansion

echo 🛑 Stopping eShop Full Stack Application...

REM Stop Backend API
echo 🔧 Stopping Backend API...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo ✅ Backend API stopped
)

REM Stop Frontend
echo 🌐 Stopping Frontend...
docker ps --filter name=eshop-frontend --format "{{.Names}}" | findstr eshop-frontend >nul 2>&1
if !errorlevel! == 0 (
    docker stop eshop-frontend >nul 2>&1
    docker rm eshop-frontend >nul 2>&1
    echo ✅ Frontend stopped
) else (
    echo ⚠️ Frontend container not running
)

REM Stop Infrastructure Services
echo 📦 Stopping Infrastructure Services...

for %%s in (eshop-keycloak eshop-rabbitmq eshop-redis eshop-postgres) do (
    docker ps --filter name=%%s --format "{{.Names}}" | findstr %%s >nul 2>&1
    if !errorlevel! == 0 (
        echo Stopping %%s...
        docker stop %%s >nul 2>&1
        docker rm %%s >nul 2>&1
        echo ✅ %%s stopped
    ) else (
        echo ⚠️ %%s not running
    )
)

REM Clean up network
echo 🧹 Cleaning up network...
docker network rm eshop-network >nul 2>&1

REM Clean up log files
if exist "backend.log" (
    del backend.log
    echo ✅ Cleaned up log files
)

echo.
echo 🎉 All services stopped successfully!

echo.
echo 📋 Final Status:
echo   • All containers stopped and removed
echo   • Network cleaned up
echo   • Log files removed

echo.
echo 🚀 To start again, run: start-all-windows.bat

pause
