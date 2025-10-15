# VS Code Debug Configurations for eShop

This directory contains VS Code configuration files for debugging the eShop application.

## Files

- `launch.json` - Debug configurations for launching applications
- `tasks.json` - Tasks for stopping servers and managing processes
- `keybindings.json` - Keyboard shortcuts for quick access
- `settings.json` - Workspace settings for Python development

## Debug Configurations

### Backend Debugging

1. **Debug Backend (FastAPI)** - Direct Python program launch
   - Runs `backend/app/main.py` directly
   - Good for debugging startup issues

2. **Debug Backend (uvicorn)** - Uvicorn-based launch with hot reload
   - Runs with `uvicorn app.main:app --reload`
   - Best for development with automatic reloading

3. **Debug Backend Tests** - Run pytest with coverage
   - Executes backend tests with coverage reporting
   - Uses test database configuration

### Frontend Debugging

1. **Debug Frontend (HTTP Server)** - Python HTTP server
   - Starts Python's built-in HTTP server on port 3000
   - Serves static HTML files from the frontend directory
   - Opens Chrome debugger automatically when server is ready

2. **Debug Frontend (Chrome)** - Browser-based debugging
   - Launches Chrome with debugging enabled
   - Good for JavaScript debugging

3. **Debug Frontend (Edge)** - Edge browser debugging
   - Alternative to Chrome debugging

### Compound Configurations

1. **Debug Full Stack (Backend + Frontend)** - Complete stack debugging
   - Starts both backend and frontend simultaneously
   - Stops all when debugging ends

2. **Debug Backend + Tests** - Backend with test runner
   - Runs backend server and test suite together

3. **Stop All Debug Sessions** - Emergency stop
   - Stops all running debug sessions

## Tasks

### Stop Tasks

1. **Stop All Development Servers** - Uses the `scripts/stop-servers.sh` script to safely stop all development servers
2. **Start Frontend Server** - Starts Python HTTP server on port 3000
3. **Stop Backend Server** - Kills uvicorn processes
4. **Stop Frontend Server** - Kills Python HTTP server processes
5. **Check Running Servers** - Shows currently running servers

**Note**: The "Stop All Development Servers" task is the recommended way to stop servers as it uses a dedicated script that:
- Safely terminates processes with SIGTERM first
- Force kills with SIGKILL if needed
- Provides detailed feedback about what's being stopped
- Checks for remaining processes

### How to Use Tasks

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "Tasks: Run Task"
3. Select the desired task

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+K` | Stop current debug session |
| `Ctrl+Shift+Alt+K` | Stop all debug sessions |
| `Ctrl+Shift+T` | Stop all development servers |
| `Ctrl+Shift+B` | Stop backend server |
| `Ctrl+Shift+F` | Stop frontend server |
| `Ctrl+Shift+C` | Check running servers |

## Usage Instructions

### Starting Debug Sessions

1. Open VS Code in the project root
2. Go to Run and Debug (Ctrl+Shift+D)
3. Select a configuration from the dropdown
4. Press F5 or click the green play button

### Stopping Debug Sessions

**Method 1: Using Debug Controls**
- Click the red stop button in the debug toolbar
- Press Shift+F5

**Method 2: Using Keyboard Shortcuts**
- `Ctrl+Shift+K` to stop current session
- `Ctrl+Shift+Alt+K` to stop all sessions

**Method 3: Using Tasks**
- `Ctrl+Shift+P` → "Tasks: Run Task" → Select stop task

### Environment Variables

All debug configurations include the necessary environment variables:
- Database connection (PostgreSQL)
- Redis connection
- RabbitMQ connection
- Keycloak configuration
- CORS settings
- Debug flags

### Troubleshooting

1. **Port Already in Use**: Use "Stop All Development Servers" task
2. **Module Not Found**: Ensure you're running from the correct directory
3. **Database Connection Issues**: Check if PostgreSQL is running
4. **Debug Session Won't Stop**: Use "Stop All Debug Sessions" compound

## Prerequisites

Before using these configurations:

1. **Install Dependencies**:
   ```bash
   cd backend && poetry install
   ```

2. **Start Infrastructure Services**:
   ```bash
   ./scripts/start-infrastructure.sh
   ```

3. **Verify Services**:
   ```bash
   ./scripts/test-launch-configs.sh
   ```

## Notes

- All configurations use the integrated terminal for better debugging experience
- Environment variables are set for local development
- Debug configurations include `justMyCode: false` for full debugging
- Compound configurations automatically stop all sessions when debugging ends
