@echo off
setlocal enabledelayedexpansion

REM =============================================================================
REM eShop FastAPI Full-Stack Development Setup for Windows
REM =============================================================================

echo.
echo ================================================================
echo  eShop FastAPI Full-Stack Development Setup for Windows
echo ================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges
) else (
    echo [WARNING] Not running as administrator. Some operations may fail.
    echo [INFO] Consider running as administrator for best results.
    echo.
)

REM Function to check if command exists
:check_command
where %1 >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] %1 is not installed or not in PATH
    set "missing_deps=!missing_deps! %1"
)
goto :eof

REM Check dependencies
echo [INFO] Checking dependencies...
set "missing_deps="

call :check_command python
call :check_command pip
call :check_command docker
call :check_command git

if defined missing_deps (
    echo.
    echo [ERROR] Missing dependencies:!missing_deps!
    echo.
    echo Please install the following:
    echo - Python 3.12+ from https://python.org
    echo - Docker Desktop from https://docker.com
    echo - Git from https://git-scm.com
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] All dependencies found!
echo.

REM Check Python version
echo [INFO] Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo Python version: %python_version%

REM Install Poetry if not present
echo [INFO] Checking Poetry installation...
where poetry >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing Poetry...
    pip install poetry
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install Poetry
        pause
        exit /b 1
    )
) else (
    echo [SUCCESS] Poetry is already installed
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating .env file from template...
    copy "env.example" ".env" >nul 2>&1
    if exist "env.example" (
        echo [SUCCESS] .env file created from env.example
    ) else (
        echo [INFO] Creating basic .env file...
        (
            echo # eShop Configuration
            echo APP_NAME="eShop Modular Monolith"
            echo DEBUG=true
            echo LOG_LEVEL=info
            echo DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/eshop
            echo REDIS_URL=redis://localhost:6379
            echo RABBITMQ_URL=amqp://guest:guest@localhost:5672/
            echo KEYCLOAK_SERVER_URL=http://localhost:8080
            echo KEYCLOAK_REALM=eshop
            echo KEYCLOAK_CLIENT_ID=eshop-api
            echo KEYCLOAK_CLIENT_SECRET=your-client-secret
        ) > .env
        echo [SUCCESS] Basic .env file created
    )
) else (
    echo [INFO] .env file already exists
)

REM Setup backend
echo.
echo [INFO] Setting up backend dependencies...
cd backend
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true
poetry install
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install backend dependencies
    cd ..
    pause
    exit /b 1
)
cd ..
echo [SUCCESS] Backend dependencies installed

REM Start Docker services
echo.
echo [INFO] Starting Docker services...
docker-compose up -d postgres redis rabbitmq keycloak
if %errorLevel% neq 0 (
    echo [ERROR] Failed to start Docker services
    echo Please ensure Docker Desktop is running
    pause
    exit /b 1
)

echo [INFO] Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Setup Keycloak
echo.
echo [INFO] Setting up Keycloak...
call setup-keycloak-windows.bat
if %errorLevel% neq 0 (
    echo [WARNING] Keycloak setup had issues, but continuing...
)

REM Run database migrations
echo.
echo [INFO] Running database migrations...
cd backend
poetry run alembic upgrade head
if %errorLevel% neq 0 (
    echo [WARNING] Database migrations had issues
)
cd ..

echo.
echo ================================================================
echo  Setup Complete!
echo ================================================================
echo.
echo Your eShop development environment is ready!
echo.
echo Next steps:
echo 1. Start the backend:
echo    cd backend
echo    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo 2. In another terminal, serve the frontend:
echo    cd frontend
echo    python -m http.server 3000
echo.
echo 3. Open your browser to:
echo    - Frontend: http://localhost:3000
echo    - Backend API: http://localhost:8000
echo    - API Docs: http://localhost:8000/docs
echo    - Keycloak Admin: http://localhost:8080/admin (admin/admin)
echo.
echo Test users:
echo - admin/password (full access)
echo - testuser/password (read-only)
echo.
pause
