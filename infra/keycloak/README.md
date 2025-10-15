# Keycloak Provisioning Guide

This guide explains how to provision Keycloak realms, clients, users, and roles using the credentials file system.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Credentials File Format](#credentials-file-format)
- [Provisioning Methods](#provisioning-methods)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Keycloak provisioning system allows you to:

- **Define all Keycloak configuration in a YAML file** (realms, clients, roles, users)
- **Avoid hardcoded credentials** in source code
- **Provision automatically** on startup or manually via CLI
- **Use realm admin** for creating roles, clients, and users (not just master admin)
- **Version control configuration** (while keeping actual credentials secure)

## Quick Start

### 1. Create Credentials File

```bash
# Copy the example file (from project root)
cp infra/keycloak/credentials.yaml.example infra/keycloak/credentials.yaml

# Edit with your credentials
nano infra/keycloak/credentials.yaml
```

**Important:** Never commit `infra/keycloak/credentials.yaml` to version control! It's already in `.gitignore`.

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Path to credentials file (optional - uses default search if not specified)
KEYCLOAK_CREDENTIALS_PATH=infra/keycloak/credentials.yaml

# Enable auto-provisioning on startup (for development)
KEYCLOAK_AUTO_PROVISION=true

# Keycloak server URL
KEYCLOAK_SERVER_URL=http://localhost:8080

# Realm name
KEYCLOAK_REALM=eshop
```

### 3. Provision Keycloak

#### Option A: CLI Script (Recommended)

```bash
# From the backend directory
cd backend

# Provision with default credentials file (searches infra/keycloak/credentials.yaml)
python scripts/provision_keycloak.py

# Provision with specific credentials file
python scripts/provision_keycloak.py ../infra/keycloak/credentials.yaml

# Validate credentials file without provisioning
python scripts/provision_keycloak.py --validate

# Show current configuration
python scripts/provision_keycloak.py --show-config
```

#### Option B: Automatic on Startup

Set `KEYCLOAK_AUTO_PROVISION=true` in your `.env` file, then start the application:

```bash
uvicorn app.main:app --reload
```

#### Option C: Python Code

```python
from app.core.auth.rbac import provision_keycloak_sync, provision_keycloak_async

# Synchronous (for scripts)
success = provision_keycloak_sync("keycloak_credentials.yaml")

# Asynchronous (for FastAPI startup)
@app.on_event("startup")
async def startup():
    success = await provision_keycloak_async()
    if success:
        logger.info("✅ Keycloak provisioned successfully")
```

## Credentials File Format

### Complete Example

```yaml
# Master Admin Credentials (for initial realm setup)
master_admin:
  username: admin
  password: admin

# Realm Admin Credentials
realm_admin:
  username: realm-admin
  email: realm-admin@eshop.com
  password: secure-password-here
  first_name: Realm
  last_name: Admin

# Application Clients
clients:
  - client_id: eshop-api
    client_secret: your-secure-client-secret
    redirect_uris:
      - "http://localhost:8000/*"
      - "https://yourdomain.com/*"
    web_origins:
      - "http://localhost:8000"
      - "https://yourdomain.com"
    service_accounts_enabled: true
    authorization_services_enabled: true
    direct_access_grants_enabled: true
    standard_flow_enabled: true

# RBAC Roles
roles:
  - name: user
    description: "Basic user role - can read data"
  - name: manager
    description: "Manager role - can read and write data"
  - name: admin
    description: "Admin role - full access to all operations"

# Application Users
users:
  - username: adminuser
    email: admin@example.com
    password: secure-password
    first_name: Admin
    last_name: User
    roles:
      - admin
    email_verified: true
    enabled: true

  - username: testuser
    email: test@example.com
    password: secure-password
    first_name: Test
    last_name: User
    roles:
      - user
    email_verified: true
    enabled: true

# Role Hierarchy Configuration
role_hierarchy:
  admin:
    includes:
      - manager
      - user
  manager:
    includes:
      - user
```

### Field Descriptions

#### Master Admin

- `username`: Keycloak master realm admin username (default: "admin")
- `password`: Keycloak master realm admin password (default: "admin")

**Note:** Used only for initial realm creation. All subsequent operations use the realm admin.

#### Realm Admin

- `username`: Username for the realm administrator
- `email`: Email address for the realm administrator
- `password`: Password for the realm administrator
- `first_name`: First name
- `last_name`: Last name

**Note:** This user will have admin privileges in your application realm and can create/manage roles, clients, and users.

#### Clients

- `client_id`: Unique client identifier
- `client_secret`: Client secret for authentication
- `redirect_uris`: List of allowed redirect URIs after authentication
- `web_origins`: List of allowed CORS origins
- `service_accounts_enabled`: Enable service accounts (for machine-to-machine)
- `authorization_services_enabled`: Enable fine-grained authorization
- `direct_access_grants_enabled`: Enable direct access (resource owner password credentials)
- `standard_flow_enabled`: Enable standard OpenID Connect flow

#### Roles

- `name`: Unique role name
- `description`: Human-readable description of the role

#### Users

- `username`: Unique username
- `email`: Email address
- `password`: User password
- `first_name`: First name
- `last_name`: Last name
- `roles`: List of role names to assign to the user
- `email_verified`: Whether email is verified (default: true)
- `enabled`: Whether user is enabled (default: true)

#### Role Hierarchy

Define composite roles (roles that include other roles):

```yaml
role_hierarchy:
  admin:
    includes:
      - manager
      - user
```

This means users with the `admin` role automatically get `manager` and `user` privileges.

## Provisioning Methods

### CLI Script

The CLI script provides the most control and feedback:

```bash
# Basic provisioning
python scripts/provision_keycloak.py

# With specific file
python scripts/provision_keycloak.py /path/to/credentials.yaml

# Validate without provisioning
python scripts/provision_keycloak.py --validate

# Show configuration
python scripts/provision_keycloak.py --show-config
```

### Automatic Provisioning

Enable automatic provisioning on application startup:

```python
# In app/main.py or your startup code
from app.config.settings import settings
from app.core.auth.rbac import provision_keycloak_async

@app.on_event("startup")
async def startup():
    if settings.keycloak_auto_provision:
        logger.info("🔧 Auto-provisioning Keycloak...")
        success = await provision_keycloak_async()
        if success:
            logger.info("✅ Keycloak provisioned successfully")
        else:
            logger.warning("⚠️ Keycloak provisioning failed")
```

### Manual Provisioning in Code

```python
from app.core.auth.rbac import (
    provision_keycloak_sync,
    provision_keycloak_async,
    validate_credentials_file,
    load_credentials_config,
)

# Validate credentials file
is_valid, message = validate_credentials_file("credentials.yaml")
if not is_valid:
    print(f"Invalid credentials: {message}")
    exit(1)

# Load configuration (without provisioning)
config = load_credentials_config("credentials.yaml")
print(f"Users: {len(config['users'])}")
print(f"Roles: {len(config['roles'])}")

# Provision synchronously
success = provision_keycloak_sync("credentials.yaml")

# Provision asynchronously
success = await provision_keycloak_async("credentials.yaml")
```

## Security Best Practices

### 1. Never Commit Credentials

The actual credentials file should **NEVER** be committed to version control:

```bash
# Already in .gitignore
keycloak_credentials.yaml
infra/keycloak/credentials.yaml
```

### 2. Use Strong Passwords

For production environments:

- Use strong, randomly generated passwords
- Never use default credentials like "admin/admin"
- Rotate credentials regularly

```bash
# Generate strong password
openssl rand -base64 32
```

### 3. Environment-Specific Files

Use different credentials files for different environments:

```bash
# Development
keycloak_credentials.dev.yaml

# Staging
keycloak_credentials.staging.yaml

# Production
keycloak_credentials.prod.yaml
```

Then reference the appropriate file:

```bash
# In .env
KEYCLOAK_CREDENTIALS_PATH=keycloak_credentials.prod.yaml
```

### 4. Secure File Permissions

Restrict access to the credentials file:

```bash
chmod 600 keycloak_credentials.yaml
```

### 5. Use Secret Management

For production, consider using a secret management system:

- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

```python
# Example: Load from AWS Secrets Manager
import boto3
import yaml

def load_credentials_from_secrets_manager():
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='keycloak-credentials')
    return yaml.safe_load(secret['SecretString'])
```

### 6. Disable Auto-Provisioning in Production

Set `KEYCLOAK_AUTO_PROVISION=false` in production and provision manually during deployment:

```bash
# During deployment
python scripts/provision_keycloak.py /path/to/prod-credentials.yaml
```

## Troubleshooting

### Issue: "Credentials file not found"

**Solution:** Ensure the credentials file exists and the path is correct:

```bash
# Check if file exists
ls -la keycloak_credentials.yaml

# Use absolute path
export KEYCLOAK_CREDENTIALS_PATH=/absolute/path/to/credentials.yaml
```

### Issue: "Failed to get master admin token"

**Solution:** Check that:

1. Keycloak is running and accessible
2. Master admin credentials are correct
3. Network connectivity to Keycloak

```bash
# Test Keycloak connectivity
curl http://localhost:8080

# Test master admin credentials
curl -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  -d "client_id=admin-cli"
```

### Issue: "Realm creation failed"

**Solution:** The realm might already exist. The system will log this as informational and continue with provisioning other resources.

### Issue: "Role assignment verification failed"

**Solution:** This might be a timing issue. The system uses retry logic, but if it persists:

1. Check Keycloak logs for errors
2. Verify the role exists in the realm
3. Manually verify the role assignment in Keycloak Admin Console

### Issue: "User token missing expected roles"

**Solution:** 

1. Verify role mappings in Keycloak Admin Console
2. Check that the client has the correct mappers configured
3. Ensure role hierarchy is properly configured

```bash
# Debug token content
python scripts/provision_keycloak.py --show-config
```

### Issue: "Invalid YAML in credentials file"

**Solution:** Validate the YAML syntax:

```bash
# Use yamllint
yamllint keycloak_credentials.yaml

# Or Python
python -c "import yaml; yaml.safe_load(open('keycloak_credentials.yaml'))"
```

### Common YAML Mistakes

```yaml
# ❌ Wrong - inconsistent indentation
users:
  - username: test
   email: test@example.com

# ✅ Correct - consistent indentation
users:
  - username: test
    email: test@example.com

# ❌ Wrong - tabs instead of spaces
users:
	- username: test

# ✅ Correct - spaces for indentation
users:
  - username: test
```

## Advanced Usage

### Custom Credentials Loader

```python
from infra.keycloak.credentials import CredentialsLoader

# Create custom loader
loader = CredentialsLoader("/custom/path/credentials.yaml")

# Load credentials
credentials = loader.load()

# Access individual components
master_admin = loader.get_master_admin()
realm_admin = loader.get_realm_admin()
clients = loader.get_clients()
roles = loader.get_roles()
users = loader.get_users()
hierarchy = loader.get_role_hierarchy()
```

### Integration with CI/CD

```yaml
# .github/workflows/provision-keycloak.yml
name: Provision Keycloak

on:
  push:
    branches: [main]

jobs:
  provision:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Create credentials file from secrets
        run: |
          echo "${{ secrets.KEYCLOAK_CREDENTIALS }}" > keycloak_credentials.yaml
      
      - name: Validate credentials
        run: |
          python scripts/provision_keycloak.py --validate
      
      - name: Provision Keycloak
        run: |
          python scripts/provision_keycloak.py
```

## Additional Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [RBAC Best Practices](https://www.keycloak.org/docs/latest/server_admin/#_rbac)

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review Keycloak logs: `docker logs keycloak`
3. Check application logs: `backend/logs/app.log`
4. Consult the team or create an issue in the project repository

