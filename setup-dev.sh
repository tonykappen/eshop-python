#!/bin/bash

echo "🚀 Setting up eShop Modular Monolith for Development..."

# Add poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Check if Python and Poetry are installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install it first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo "✅ Python and Poetry are available"

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating default configuration..."
    cat > .env << 'EOF'
# Application Configuration
APP_NAME=eShop Modular Monolith
APP_VERSION=0.1.0
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://eshop_user:eshop_password@localhost:5432/eshop
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=eshop
DATABASE_USER=eshop_user
DATABASE_PASSWORD=eshop_password

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
    echo "✅ .env file created"
fi

echo ""
echo "🎯 Development Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Start PostgreSQL (if not running): brew services start postgresql"
echo "2. Start Redis (if not running): brew services start redis"
echo "3. Start RabbitMQ (if not running): brew services start rabbitmq"
echo "4. Run the application: poetry run uvicorn eshop.main:app --reload"
echo ""
echo "🌐 Application will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "💡 For Docker setup (when Docker is available): ./setup-docker.sh" 