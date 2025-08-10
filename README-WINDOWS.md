# eShop Python FastAPI - Windows Setup Guide

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

> **Complete Windows setup guide for the eShop Python FastAPI application with RBAC authentication**

## 🚀 Quick Start (TL;DR)

1. **Install Prerequisites**: Python 3.12+, Docker Desktop
2. **Run Complete Setup**: `setup-complete-windows.bat`
3. **Test**: Open http://localhost:8000/docs

**OR Step by Step:**
1. **Run Setup**: `setup-dev-windows.bat`
2. **Start Services**: `setup-docker-windows.bat`
3. **Configure Auth**: `setup-keycloak-windows.bat`

---

## 📋 Prerequisites

### Required Software

| Software | Version | Download Link | Notes |
|----------|---------|---------------|-------|
| **Python** | 3.12+ | [python.org](https://python.org/downloads/) | ✅ Check "Add Python to PATH" |
| **Docker Desktop** | Latest | [docker.com](https://docker.com/products/docker-desktop) | ✅ Enable WSL 2 backend |
| **Git** | Latest | [git-scm.com](https://git-scm.com/download/win) | ⚠️ Optional but recommended |

### Optional Tools

| Tool | Purpose | Download Link |
|------|---------|---------------|
| **curl** | API testing | [curl.se](https://curl.se/windows/) |
| **jq** | JSON parsing | [stedolan.github.io/jq](https://stedolan.github.io/jq/download/) |
| **Windows Terminal** | Better terminal | [Microsoft Store](https://aka.ms/terminal) |

---

## 🛠️ Installation Methods

### Method 1: One-Click Setup (Recommended)

1. Download and extract the project
2. Open Command Prompt as Administrator
3. Navigate to the project folder
4. Run the complete setup:
   ```cmd
   setup-complete-windows.bat
   ```

### Method 2: Step-by-Step Setup

#### Step 1: Development Environment
```cmd
setup-dev-windows.bat
```

#### Step 2: Docker Services
```cmd
setup-docker-windows.bat
```

#### Step 3: Authentication Setup
```cmd
setup-keycloak-windows.bat
```

---

## 🎯 Testing the Application

### 1. Verify Services are Running

Open your browser and check these URLs:

| Service | URL | Expected Result |
|---------|-----|-----------------|
| **Backend API** | http://localhost:8000/docs | FastAPI Swagger UI |
| **Health Check** | http://localhost:8000/health | `{"status": "ok"}` |
| **Frontend** | http://localhost:3000 | Login page |
| **Keycloak** | http://localhost:8080/admin | Admin console (admin/admin) |
| **RabbitMQ** | http://localhost:15672 | Management UI (guest/guest) |

### 2. Test Authentication

**Get User Token (Read-Only Access):**
```cmd
curl -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token ^
  -d "username=user&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret"
```

**Get Admin Token (Full Access):**
```cmd
curl -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token ^
  -d "username=admin&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret"
```

### 3. Test API Endpoints

**Get Products (Any Role):**
```cmd
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/catalog/products
```

**Create Product (Admin/Manager Only):**
```cmd
curl -X POST -H "Authorization: Bearer YOUR_ADMIN_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Test Product\",\"description\":\"Test\",\"price\":99.99,\"picture_url\":\"http://example.com/pic.jpg\"}" ^
  http://localhost:8000/api/v1/catalog/products
```

---

## 👥 User Accounts

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| **admin** | password | Admin | Full access (Read/Write/Delete) |
| **manager** | password | Manager | Read/Write access |
| **user** | password | User | Read-only access |

---

## 🔧 Development Commands

### Starting the Application

```cmd
cd backend
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Code Quality

```cmd
cd backend

REM Format code
poetry run black app/

REM Check linting
poetry run ruff check app/ --fix

REM Type checking
poetry run mypy app/ --ignore-missing-imports

REM Run tests
poetry run pytest tests/ -v
```

### Docker Management

```cmd
REM View running containers
docker-compose ps

REM View logs
docker-compose logs -f

REM Restart specific service
docker-compose restart [service-name]

REM Stop all services
docker-compose down

REM Clean up everything
docker-compose down -v --remove-orphans
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **"Python is not recognized"**
- **Solution**: Reinstall Python and check "Add Python to PATH"
- **Verify**: `python --version` should work

#### 2. **"Poetry is not recognized"**
- **Solution**: 
  ```cmd
  python -m pip install --user poetry
  # Then restart Command Prompt
  ```

#### 3. **"Docker is not running"**
- **Solution**: Start Docker Desktop from Start Menu
- **Verify**: `docker --version` should work

#### 4. **Port Already in Use**
- **Check what's using the port**:
  ```cmd
  netstat -ano | findstr :8000
  ```
- **Kill the process**:
  ```cmd
  taskkill /PID [PID_NUMBER] /F
  ```

#### 5. **Database Connection Failed**
- **Check PostgreSQL container**: `docker-compose logs postgres`
- **Restart database**: `docker-compose restart postgres`
- **Verify .env settings** in `backend/.env`

#### 6. **Keycloak Setup Failed**
- **Wait longer**: Keycloak takes 2-3 minutes to fully start
- **Check container**: `docker-compose logs keycloak`
- **Restart setup**: Run `setup-keycloak-windows.bat` again

### Log Files

| Component | Log Location |
|-----------|--------------|
| **Application** | `backend/logs/` |
| **Docker Services** | `docker-compose logs [service]` |
| **Windows Event** | Event Viewer → Application |

### Health Checks

```cmd
REM Check all service health
curl http://localhost:8000/health/detailed

REM Check specific components
curl http://localhost:8000/health/database
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/rabbitmq
curl http://localhost:8000/health/keycloak
```

---

## 📁 Project Structure

```
eShop/
├── 📁 backend/
│   ├── 📁 app/                 # Main application code
│   │   ├── 📁 core/           # Core functionality
│   │   ├── 📁 modules/        # Business modules
│   │   └── main.py            # Application entry point
│   ├── 📁 tests/              # Test files
│   ├── 📁 logs/               # Application logs
│   ├── .env                   # Environment variables
│   └── pyproject.toml         # Python dependencies
├── 📁 frontend/               # Frontend files
├── 📁 docs/                   # Documentation
├── docker-compose.yml         # Docker services
├── setup-complete-windows.bat # Complete setup (recommended)
├── setup-dev-windows.bat      # Development setup
├── setup-docker-windows.bat   # Docker setup
├── setup-keycloak-windows.bat # Authentication setup
└── README-WINDOWS.md          # This file
```

---

## 🚀 Production Deployment

### Environment Variables

Update `backend/.env` for production:

```env
# Production Database
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/eshop

# Production Keycloak
KEYCLOAK_URL=https://auth.yourdomain.com
KEYCLOAK_CLIENT_SECRET=your-production-secret

# Security
LOG_LEVEL=WARNING
LOG_REQUEST_BODY=false
LOG_RESPONSE_BODY=false
```

### SSL/HTTPS

1. Update `CORS_ORIGINS` in `.env`
2. Configure reverse proxy (nginx/IIS)
3. Set up SSL certificates

---

## 🆘 Getting Help

### Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Poetry Documentation**: https://python-poetry.org/docs/
- **Docker Documentation**: https://docs.docker.com/
- **Keycloak Documentation**: https://keycloak.org/documentation

### Support

1. **Check logs** first (application and Docker)
2. **Search issues** in the project repository
3. **Create detailed issue** with:
   - Windows version
   - Error messages
   - Steps to reproduce
   - Log files

---

## ✅ Quick Checklist

- [ ] Python 3.12+ installed and in PATH
- [ ] Docker Desktop installed and running
- [ ] Project extracted to local folder
- [ ] Ran `setup-complete-windows.bat` successfully
- [ ] Can access http://localhost:8000/docs
- [ ] Can login with test users
- [ ] API endpoints working with proper RBAC

---

**🎉 Congratulations! Your eShop development environment is ready!**

For questions or issues, refer to the troubleshooting section above or check the project documentation.

---

*Last updated: 2024*
