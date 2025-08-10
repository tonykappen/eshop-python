# ==============================================================================
# Development Environment Setup Script for Windows (PowerShell) - eShop Python FastAPI
# ==============================================================================

Write-Host ""
Write-Host "===================================================================" -ForegroundColor Blue
Write-Host "        🚀 Setting up eShop Development Environment (Windows)" -ForegroundColor Blue
Write-Host "===================================================================" -ForegroundColor Blue
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) { return $true }
    }
    catch { return $false }
}

# Check if Python is installed
if (-not (Test-Command "python")) {
    Write-Host "❌ Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.12+ from https://python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "✅ $pythonVersion detected" -ForegroundColor Green

# Check if Poetry is installed
if (-not (Test-Command "poetry")) {
    Write-Host "❌ Poetry is not installed. Installing Poetry..." -ForegroundColor Red
    Write-Host ""
    Write-Host "Installing Poetry via pip..." -ForegroundColor Yellow
    python -m pip install --user poetry
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install Poetry" -ForegroundColor Red
        Write-Host "Please install Poetry manually from https://python-poetry.org/docs/#installation" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "✅ Poetry installed successfully" -ForegroundColor Green
    
    # Refresh PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
} else {
    $poetryVersion = poetry --version 2>&1
    Write-Host "✅ $poetryVersion detected" -ForegroundColor Green
}

# Check if Git is installed
if (-not (Test-Command "git")) {
    Write-Host "⚠️  Warning: Git is not installed" -ForegroundColor Yellow
    Write-Host "You can install Git from https://git-scm.com/download/win" -ForegroundColor Yellow
} else {
    $gitVersion = git --version 2>&1
    Write-Host "✅ $gitVersion detected" -ForegroundColor Green
}

# Check if Docker is available
$dockerAvailable = $false
if (Test-Command "docker") {
    $dockerVersion = docker --version 2>&1
    Write-Host "✅ $dockerVersion detected" -ForegroundColor Green
    $dockerAvailable = $true
} else {
    Write-Host "⚠️  Warning: Docker is not installed" -ForegroundColor Yellow
    Write-Host "You can install Docker Desktop from https://docker.com/products/docker-desktop" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Setting up Python dependencies..." -ForegroundColor Blue

# Navigate to backend directory
if (-not (Test-Path "backend")) {
    Write-Host "❌ Error: backend directory not found" -ForegroundColor Red
    Write-Host "Please run this script from the eShop project root directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Set-Location backend

# Install dependencies with Poetry
Write-Host "Installing Python dependencies with Poetry..." -ForegroundColor Yellow
poetry install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Python dependencies installed successfully" -ForegroundColor Green

# Set up pre-commit hooks
Write-Host ""
Write-Host "🔧 Setting up pre-commit hooks..." -ForegroundColor Blue
poetry run pre-commit install
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Failed to install pre-commit hooks" -ForegroundColor Yellow
} else {
    Write-Host "✅ Pre-commit hooks installed" -ForegroundColor Green
}

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "✅ Created logs directory" -ForegroundColor Green
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file with default values..." -ForegroundColor Blue
    
    $envContent = @"
# eShop Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_REQUEST_BODY=false
LOG_RESPONSE_BODY=false

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=eshop
DB_USER=postgres
DB_PASSWORD=postgres
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/eshop

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest

# Keycloak Configuration
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=eshop
KEYCLOAK_CLIENT_ID=eshop-api
KEYCLOAK_CLIENT_SECRET=your-client-secret

# API Configuration
API_V1_PREFIX=/api/v1

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Created .env file with default configuration" -ForegroundColor Green
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "🔍 Running code quality checks..." -ForegroundColor Blue

Set-Location backend

# Run linting and formatting
Write-Host "Running Ruff checks..." -ForegroundColor Yellow
poetry run ruff check app/ --fix
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Ruff found some issues that couldn't be auto-fixed" -ForegroundColor Yellow
}

Write-Host "Running Black formatting..." -ForegroundColor Yellow
poetry run black app/
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Black formatting failed" -ForegroundColor Yellow
}

Write-Host "Running MyPy type checking..." -ForegroundColor Yellow
poetry run mypy app/ --ignore-missing-imports
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  MyPy found type issues" -ForegroundColor Yellow
}

Set-Location ..

Write-Host ""
Write-Host "🐳 Docker Services Setup..." -ForegroundColor Blue

if ($dockerAvailable) {
    Write-Host "Checking if Docker services are needed..." -ForegroundColor Yellow
    if (Test-Path "docker-compose.yml") {
        Write-Host "Found docker-compose.yml" -ForegroundColor Green
        Write-Host "You can start services with: docker-compose up -d" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Starting essential services (PostgreSQL, Redis, RabbitMQ, Keycloak)..." -ForegroundColor Yellow
        docker-compose up -d postgres redis rabbitmq keycloak
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Failed to start some Docker services" -ForegroundColor Yellow
            Write-Host "You may need to start them manually" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Essential Docker services started" -ForegroundColor Green
            Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
            Start-Sleep -Seconds 30
        }
    } else {
        Write-Host "⚠️  docker-compose.yml not found" -ForegroundColor Yellow
        Write-Host "You'll need to set up PostgreSQL, Redis, RabbitMQ, and Keycloak manually" -ForegroundColor Yellow
    }
} else {
    Write-Host "Docker not available. You'll need to install and configure:" -ForegroundColor Yellow
    Write-Host "  - PostgreSQL (port 5432)" -ForegroundColor Yellow
    Write-Host "  - Redis (port 6379)" -ForegroundColor Yellow
    Write-Host "  - RabbitMQ (port 5672)" -ForegroundColor Yellow
    Write-Host "  - Keycloak (port 8080)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 Database Setup..." -ForegroundColor Blue

Set-Location backend

Write-Host "Running database migrations..." -ForegroundColor Yellow
poetry run alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Database migration failed" -ForegroundColor Yellow
    Write-Host "Make sure PostgreSQL is running and accessible" -ForegroundColor Yellow
} else {
    Write-Host "✅ Database migrations completed" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "🎉 Development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 What was set up:" -ForegroundColor Blue
Write-Host "  ✅ Python dependencies installed with Poetry" -ForegroundColor Green
Write-Host "  ✅ Pre-commit hooks configured" -ForegroundColor Green
Write-Host "  ✅ .env file created with default configuration" -ForegroundColor Green
Write-Host "  ✅ Code quality tools configured (Ruff, Black, MyPy)" -ForegroundColor Green
Write-Host "  ✅ Database migrations applied" -ForegroundColor Green
if ($dockerAvailable) {
    Write-Host "  ✅ Docker services started" -ForegroundColor Green
}
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Blue
Write-Host "  1. Review and update the .env file with your specific configuration" -ForegroundColor Yellow
Write-Host "  2. Run Keycloak setup: .\setup-keycloak-windows.bat" -ForegroundColor Yellow
Write-Host "  3. Start the development server:" -ForegroundColor Yellow
Write-Host "     cd backend" -ForegroundColor Cyan
Write-Host "     poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Application URLs (once started):" -ForegroundColor Blue
Write-Host "  • Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  • API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  • Frontend: http://localhost:3000 (if using the frontend)" -ForegroundColor Cyan
Write-Host "  • Keycloak Admin: http://localhost:8080/admin/ (admin/admin)" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔧 Useful Commands:" -ForegroundColor Blue
Write-Host "  • Run tests: cd backend && poetry run pytest" -ForegroundColor Cyan
Write-Host "  • Code formatting: cd backend && poetry run black app/" -ForegroundColor Cyan
Write-Host "  • Linting: cd backend && poetry run ruff check app/" -ForegroundColor Cyan
Write-Host "  • Type checking: cd backend && poetry run mypy app/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Happy coding! 🎯" -ForegroundColor Green
Read-Host "Press Enter to exit"
