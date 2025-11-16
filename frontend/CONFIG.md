# Frontend Configuration Guide

This document explains how to configure the frontend application.

## Security Update

**IMPORTANT**: As of the latest update, `KEYCLOAK_CLIENT_SECRET` is **NO LONGER NEEDED** in the frontend. Client credentials are now handled **server-side only** to prevent exposure in browser network requests.

The frontend only needs:
- `API_BASE` - Backend API URL
- `KEYCLOAK_SERVER_URL` - For debugging/realm info only
- `KEYCLOAK_REALM` - For debugging/realm info only

**Client credentials (`client_id` and `client_secret`) are handled by the backend automatically.**

## Problem (Historical)

Previously, the frontend needed access to configuration values like:
- `KEYCLOAK_CLIENT_ID`
- `KEYCLOAK_CLIENT_SECRET` ⚠️ **NO LONGER USED IN FRONTEND**
- `API_BASE`
- `KEYCLOAK_SERVER_URL`
- `KEYCLOAK_REALM`

These values should **NOT** be hardcoded in the source code, especially secrets.

## Solution

We use a `config.js` file that can be generated from environment variables.

## Usage

### Development (Local)

1. **Option 1: Generate from .env file**
   ```bash
   cd frontend
   source ../.env  # Load environment variables
   ./generate-config.sh > config.js
   ```

2. **Option 2: Generate with Node.js**
   ```bash
   cd frontend
   KEYCLOAK_CLIENT_SECRET=your-secret node generate-config.js
   ```

3. **Option 3: Manual edit (not recommended)**
   - Edit `config.js` directly
   - **WARNING**: Do not commit secrets to git!

### Production (Docker)

Add to your Dockerfile or docker-compose.yml:

```dockerfile
# In Dockerfile
RUN node generate-config.js

# Or use envsubst
RUN envsubst < config.js.template > config.js
```

Or in docker-compose.yml:
```yaml
frontend:
  build:
    context: ./frontend
  environment:
    - KEYCLOAK_CLIENT_SECRET=${KEYCLOAK_CLIENT_SECRET}
  # Use entrypoint script to generate config.js at runtime
```

### Using in HTML Files

All HTML files should load `config.js` first:

```html
<script src="config.js"></script>
<script>
    const CLIENT_ID = window.APP_CONFIG?.KEYCLOAK_CLIENT_ID || 'eshop-api';
    const CLIENT_SECRET = window.APP_CONFIG?.KEYCLOAK_CLIENT_SECRET || '';
    
    // Use CLIENT_ID and CLIENT_SECRET in your code
</script>
```

## Environment Variables

Set these in your `.env` file (not committed to git):

```bash
API_BASE=http://localhost:8000
KEYCLOAK_CLIENT_ID=eshop-api
KEYCLOAK_CLIENT_SECRET=your-secret-here
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=eshop
```

## Security Best Practices

1. ✅ **DO**: Use the backend proxy for authentication (handles credentials server-side)
2. ✅ **DO**: Never send `client_secret` from the frontend
3. ✅ **DO**: Use environment variables for backend configuration
4. ✅ **DO**: Generate `config.js` from env vars during build/deployment (if needed)
5. ❌ **DON'T**: Hardcode secrets in HTML/JS files
6. ❌ **DON'T**: Send `client_id` or `client_secret` in API requests from frontend
7. ❌ **DON'T**: Expose secrets in client-side code - always use backend proxy

## Files Updated

The following files have been updated to use `config.js`:
- `frontend/index.html`
- `frontend/debug.html`
- `frontend/config.js` (new)
- `frontend/generate-config.sh` (new)
- `frontend/generate-config.js` (new)

## VS Code Launch Configuration

The `.vscode/launch.json` has been updated to:
- Use `envFile` to load environment variables from `.env`
- Remove hardcoded `KEYCLOAK_CLIENT_SECRET`

Make sure your `.env` file contains:
```
KEYCLOAK_CLIENT_SECRET=your-secret-here
```

